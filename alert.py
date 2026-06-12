import time
import requests
from datetime import datetime
from config import DEPT_WEBHOOKS, DEFAULT_WEBHOOK
from utils import cell_val, cell_num

def send_msg(webhook, text):
    r = requests.post(webhook, json={
        "msg_type": "text",
        "content": {"text": text}
    }, timeout=10).json()
    return r.get("code") == 0 or r.get("StatusCode") == 0

def build_msg(dept, records):
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    红 = [r for r in records if cell_val(r["fields"].get("健康度")) == "预警"]
    黄 = [r for r in records if cell_val(r["fields"].get("健康度")) == "关注"]
    lines = []
    lines.append(f"📋 {dept}招聘健康度播报 · {today}")
    lines.append(f"共 {len(红)} 个预警 · {len(黄)} 个关注\n")
    if 红:
        lines.append("🔴 需立即处理")
        for r in 红:
            f = r["fields"]
            name     = cell_val(f.get("岗位名称"))
            stage    = cell_val(f.get("当前主要阶段"))
            reason   = cell_val(f.get("预警原因"))
            owner    = r.get("_job_cfg", {}).get("招聘负责人HR", "")
            days     = cell_num(f, "该阶段停留天数")
            cv7      = cell_num(f, "近7天新增简历")
            priority = r.get("_job_cfg", {}).get("岗位优先级", "P1")
            lines.append(f"▸ [{priority}] {name}（{owner}）")
            lines.append(f"  阶段：{stage} · 停留{days}天 · 近7天{cv7}份")
            if reason: lines.append(f"  原因：{reason}")
        lines.append("")
    if 黄:
        lines.append("🟡 需关注跟进")
        for r in 黄:
            f = r["fields"]
            name     = cell_val(f.get("岗位名称"))
            stage    = cell_val(f.get("当前主要阶段"))
            reason   = cell_val(f.get("预警原因"))
            owner    = r.get("_job_cfg", {}).get("招聘负责人HR", "")
            days     = cell_num(f, "该阶段停留天数")
            cv7      = cell_num(f, "近7天新增简历")
            priority = r.get("_job_cfg", {}).get("岗位优先级", "P1")
            lines.append(f"▸ [{priority}] {name}（{owner}）")
            lines.append(f"  阶段：{stage} · 停留{days}天 · 近7天{cv7}份")
            if reason: lines.append(f"  原因：{reason}")
    return "\n".join(lines)

def send_dept_alerts(records):
    dept_map = {}
    for rec in records:
        f = rec["fields"]
        health = cell_val(f.get("健康度"))
        if health not in ("预警", "关注"): continue
        dept = rec.get("_dept") or cell_val(f.get("所属部门")) or "未知部门"
        dept_map.setdefault(dept, []).append(rec)
    if not dept_map:
        print("没有预警或关注的岗位，无需推送")
        return
    for dept, recs in dept_map.items():
        webhook = DEPT_WEBHOOKS.get(dept, DEFAULT_WEBHOOK)
        target = dept if dept in DEPT_WEBHOOKS else f"{dept}（→总群）"
        msg = build_msg(dept, recs)
        ok = send_msg(webhook, msg)
        print(f"{'✅' if ok else '❌'} {target}: 推送{len(recs)}条")
        time.sleep(0.3)
