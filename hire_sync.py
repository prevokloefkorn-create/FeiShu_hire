#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书招聘API -> 候选人明细表（表3）同步脚本
等HR开通招聘后台数据权限后运行
运行：python3 hire_sync.py
"""
import time, requests
from datetime import datetime, timezone
from config import APP_ID, APP_SECRET, BASE, APP_TOKEN, TABLE_ID_CAND
from utils import get_token, req_with_retry

PAGE_SIZE = 20

def days_since(ms):
    if not ms: return None
    try:
        dt = datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except: return None

def ts_to_date(ms):
    if not ms: return None
    try:
        return int(ms)
    except: return None

# 阶段名映射（根据你们飞书招聘实际阶段名调整）
STAGE_MAP = {
    "待筛选": "筛选", "简历筛选": "筛选", "筛选": "筛选",
    "评估": "评估", "笔试": "评估",
    "初试": "面试", "复试": "面试", "终面": "面试", "面试": "面试",
    "offer": "Offer", "Offer": "Offer", "offer审批": "Offer",
    "待入职": "待入职",
    "已入职": "已入职",
}

def get_jobs(token):
    jobs, page_token = [], None
    while True:
        params = {"page_size": PAGE_SIZE}
        if page_token: params["page_token"] = page_token
        d, err = req_with_retry("GET", f"{BASE}/hire/v1/jobs", token, params=params)
        if err or not d or d.get("code") != 0:
            print(f"[拉职位失败] {err or d.get('msg')}")
            break
        data = d.get("data", {})
        jobs.extend(data.get("items", []))
        if not data.get("has_more"): break
        page_token = data.get("page_token")
    return jobs

def get_applications(token, job_id):
    apps, page_token = [], None
    while True:
        params = {"page_size": PAGE_SIZE, "job_id": job_id}
        if page_token: params["page_token"] = page_token
        d, err = req_with_retry("GET", f"{BASE}/hire/v1/applications", token, params=params)
        if err or not d or d.get("code") != 0: break
        data = d.get("data", {})
        apps.extend(data.get("items", []))
        if not data.get("has_more"): break
        page_token = data.get("page_token")
    return apps

def get_talent(token, talent_id):
    d, err = req_with_retry("GET", f"{BASE}/hire/v1/talents/{talent_id}", token)
    if err or not d or d.get("code") != 0: return {}
    return d.get("data", {}).get("talent", {})

def clear_table(token):
    """清空表3，重新写入最新数据"""
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID_CAND}/records/search"
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    items = []
    page_token = None
    while True:
        body = {"page_size": 100}
        if page_token: body["page_token"] = page_token
        d = requests.post(url, headers=h, json=body).json()
        if d.get("code") != 0: break
        data = d.get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"): break
        page_token = data.get("page_token")
    if not items: return
    # 批量删除
    record_ids = [r["record_id"] for r in items]
    for i in range(0, len(record_ids), 500):
        batch = record_ids[i:i+500]
        requests.delete(
            f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID_CAND}/records/batch_delete",
            headers=h, json={"records": batch})
    print(f"✅ 清空表3 {len(record_ids)} 条旧数据")

def write_candidates(token, candidates):
    if not candidates: return
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID_CAND}/records/batch_create"
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_ok = 0
    for i in range(0, len(candidates), 100):
        batch = candidates[i:i+100]
        d = requests.post(url, headers=h,
            json={"records": [{"fields": c} for c in batch]}).json()
        if d.get("code") == 0:
            total_ok += len(batch)
        else:
            print(f"  [写入失败] {d.get('msg')}")
        time.sleep(0.2)
    print(f"✅ 写入候选人 {total_ok}/{len(candidates)} 条")

def main():
    token = get_token()
    print("✅ 换token成功")

    jobs = get_jobs(token)
    print(f"✅ 拉到 {len(jobs)} 个职位")

    if not jobs:
        print("没有职位数据，请确认：")
        print("  1. 飞书招聘后台已给应用授权数据权限")
        print("  2. 运行 python3 feishu_sync_real.py --probe 验证")
        return

    candidates = []
    for job in jobs:
        job_id   = job.get("id") or job.get("job_id")
        job_name = job.get("title") or job.get("name") or "?"
        apps = get_applications(token, job_id)
        print(f"  {job_name}: {len(apps)} 条投递")

        for app in apps:
            app_id     = app.get("id") or app.get("application_id")
            talent_id  = app.get("talent_id")
            stage      = app.get("stage", {})
            stage_name = stage.get("name", "") if isinstance(stage, dict) else ""
            stage_mapped = STAGE_MAP.get(stage_name, stage_name or "筛选")
            create_time = app.get("create_time")
            update_time = app.get("update_time") or app.get("modify_time")

            # 拉候选人姓名
            name = "?"
            if talent_id:
                talent = get_talent(token, talent_id)
                name = talent.get("name") or "?"
                time.sleep(0.05)

            candidates.append({
                "候选人姓名":        name,
                "应聘岗位":         job_name,
                "当前阶段":         stage_mapped,
                "进入当前阶段时间":  ts_to_date(update_time),
                "简历来源":         app.get("delivery_type", ""),
                "候选人状态":       "进行中" if stage_mapped not in ("已入职",) else "已入职",
                "备注":            f"application_id:{app_id}",
            })
        time.sleep(0.1)

    print(f"\n共 {len(candidates)} 条候选人数据，开始写入表3...")
    clear_table(token)
    write_candidates(token, candidates)
    print("\n完成！")

if __name__ == "__main__":
    main()
