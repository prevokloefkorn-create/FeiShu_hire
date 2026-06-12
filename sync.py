#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from datetime import datetime, timezone
from config import STAGE_ORDER, BATCH_SIZE, BATCH_SLEEP, TABLE_ID_BOARD, TABLE_ID_CAND
from utils import get_token, cell_val, cell_num, cell_date_days
from health import calc_main_stage, calc_health
from bitable import get_records, get_job_configs, get_job_open_dates, update_record, write_history
from aggregate import aggregate_candidates, calc_completion_rate, calc_time_progress
from alert import send_dept_alerts
from notify import notify_result

def main():
    start = time.time()
    token = get_token()
    print("✅ 换token成功")

    job_configs = get_job_configs(token)
    print(f"✅ 读取表1配置 {len(job_configs)} 个岗位")

    job_dates = get_job_open_dates(token)
    print(f"✅ 读取表1日期 {len(job_dates)} 个岗位")

    cand_records = get_records(token, TABLE_ID_CAND)
    print(f"✅ 读取表3候选人 {len(cand_records)} 条")
    cand_agg = aggregate_candidates(cand_records)
    print(f"✅ 聚合 {len(cand_agg)} 个岗位的候选人数据")

    records = get_records(token, TABLE_ID_BOARD)
    print(f"✅ 读取看板 {len(records)} 条记录，开始计算...\n")

    ok, fail, changed = 0, 0, 0
    error_names = []
    snapshots = []
    now_ts = int(datetime.now().timestamp() * 1000)

    for i, rec in enumerate(records):
        if i > 0 and i % BATCH_SIZE == 0:
            print(f"  [节流] 已处理{i}条，休眠{BATCH_SLEEP}秒...")
            time.sleep(BATCH_SLEEP)
        try:
            f = rec["fields"]
            rid = rec["record_id"]
            name = cell_val(f.get("岗位名称")) or "?"

            job_cfg   = job_configs.get(name, {})
            job_date  = job_dates.get(name, {})
            dept      = job_cfg.get("所属部门") or cell_val(f.get("所属部门")) or "未知部门"
            priority  = job_cfg.get("岗位优先级") or cell_val(f.get("岗位优先级")).strip() or "P1"
            开启天数   = job_cfg.get("开启天数")
            计划人数   = job_cfg.get("计划招聘人数") or cell_num(f, "计划招聘人数")

            agg = cand_agg.get(name)
            if agg:
                stage_counts = {s: agg.get(s, 0) for s in STAGE_ORDER}
                在投   = agg["在投简历数"]
                近7天  = agg["近7天新增简历"]
                停留天数 = agg["该阶段停留天数"]
            else:
                stage_counts = {s: cell_num(f, s) for s in STAGE_ORDER}
                在投   = stage_counts["筛选"] + stage_counts["评估"] + stage_counts["面试"] + stage_counts["Offer"]
                近7天  = cell_num(f, "近7天新增简历")
                停留天数 = cell_num(f, "该阶段停留天数")

            已入职 = stage_counts["已入职"]

            # 完成率和时间进度
            完成率  = calc_completion_rate(已入职, 计划人数)
            时间进度 = calc_time_progress(
                job_date.get("岗位开启日期_ms"),
                job_date.get("目标完成日期_ms")
            )

            f["在投简历数"]    = 在投
            f["近7天新增简历"]  = 近7天
            f["该阶段停留天数"] = 停留天数
            f["开启天数"]      = 开启天数
            for s in STAGE_ORDER:
                f[s] = stage_counts[s]

            main_stage = calc_main_stage(f)
            old_health = cell_val(f.get("上次健康度")) or ""
            health, reason = calc_health(f, job_config=job_cfg)
            is_changed = old_health != health
            if is_changed: changed += 1

            开启说明 = f"开启{开启天数}天" if 开启天数 else ""
            src = "表3" if agg else "表4"

            new_fields = {
                "在投简历数":    在投,
                "已入职数":     已入职,
                "完成率":       完成率,
                "时间进度":     时间进度,
                "筛选":        stage_counts["筛选"],
                "评估":        stage_counts["评估"],
                "面试":        stage_counts["面试"],
                "Offer":      stage_counts["Offer"],
                "待入职":      stage_counts["待入职"],
                "已入职":      stage_counts["已入职"],
                "近7天新增简历": 近7天,
                "该阶段停留天数": 停留天数,
                "当前主要阶段":  main_stage,
                "健康度":       health,
                "预警原因":     reason,
                "上次健康度":    old_health,
            }

            success, msg = update_record(token, TABLE_ID_BOARD, rid, new_fields)
            if success:
                tag = "🔴" if health == "预警" else "🟡" if health == "关注" else "🟢"
                change_flag = " ⚡变化" if is_changed else ""
                print(f"{tag} [{priority}][{src}] {name} [{开启说明}] 完成率{完成率}% 时间进度{时间进度}%: {main_stage} | {health}"
                      + (f" ({reason})" if reason else "") + change_flag)
                if is_changed:
                    update_record(token, TABLE_ID_BOARD, rid, {"上次健康度": health})
                ok += 1
                snapshots.append({
                    "记录时间":    now_ts,
                    "岗位名称":    name,
                    "在投简历数":  在投,
                    "筛选":       stage_counts["筛选"],
                    "评估":       stage_counts["评估"],
                    "面试":       stage_counts["面试"],
                    "Offer":     stage_counts["Offer"],
                    "健康度":     health,
                    "预警原因":   reason,
                })
                rec["_dept"]    = dept
                rec["_job_cfg"] = job_cfg
            else:
                print(f"❌ {name}: {msg}")
                error_names.append(name)
                fail += 1
        except Exception as e:
            name = cell_val(rec.get("fields", {}).get("岗位名称")) or "?"
            print(f"❌ {name} 异常: {e}")
            error_names.append(name)
            fail += 1

    print(f"\n写入历史快照...")
    write_history(token, snapshots)

    if changed > 0:
        print(f"\n健康度有变化，开始分部门推送...")
        send_dept_alerts(records)
    else:
        print(f"\n健康度无变化，跳过推送")

    duration = round(time.time() - start, 1)
    print(f"\n完成：成功{ok}条，失败{fail}条，变化{changed}条，耗时{duration}秒")
    notify_result(ok, fail, changed, duration, error_names)

if __name__ == "__main__":
    main()
