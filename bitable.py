from datetime import datetime, timezone
from config import BASE, APP_TOKEN, TABLE_ID_BOARD, TABLE_ID_LOG, TABLE_ID_JOB
from utils import req_with_retry, cell_val, cell_num

def _days_since(ms):
    if not ms: return None
    try:
        dt = datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except: return None

def get_records(token, table_id):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/records/search"
    items, page_token = [], None
    while True:
        body = {"page_size": 100}
        if page_token: body["page_token"] = page_token
        d, err = req_with_retry("POST", url, token, json=body)
        if err or not d or d.get("code") != 0: break
        data = d.get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"): break
        page_token = data.get("page_token")
    return items

def get_job_configs(token):
    records = get_records(token, TABLE_ID_JOB)
    configs = {}
    for rec in records:
        f = rec["fields"]
        name = cell_val(f.get("岗位名称"))
        if not name: continue
        configs[name] = {
            "所属部门":           cell_val(f.get("所属部门")),
            "岗位优先级":         cell_val(f.get("岗位优先级")),
            "预警阈值-停留天数":   cell_num(f, "预警阈值-停留天数"),
            "预警阈值-7天简历数":  cell_num(f, "预警阈值-7天简历数"),
            "招聘负责人HR":       cell_val(f.get("招聘负责人HR")),
            "面试官":            cell_val(f.get("面试官")),
            "岗位专属群ID":       cell_val(f.get("岗位专属群ID")),
            "计划招聘人数":       cell_num(f, "计划招聘人数"),
            "目标完成日期":       f.get("目标完成日期"),
            "开启天数":          _days_since(f.get("岗位开启日期")),
        }
    return configs

def update_record(token, table_id, record_id, fields):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/records/{record_id}"
    d, err = req_with_retry("PUT", url, token, json={"fields": fields})
    if err: return False, err
    return d.get("code") == 0, d.get("msg", "")

def add_record(token, table_id, fields):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/records"
    d, err = req_with_retry("POST", url, token, json={"fields": fields})
    if err: return False, err
    return d.get("code") == 0, d.get("msg", "")

def write_history(token, snapshots):
    if not snapshots: return
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID_LOG}/records/batch_create"
    total_ok = 0
    for i in range(0, len(snapshots), 100):
        batch = snapshots[i:i+100]
        d, err = req_with_retry("POST", url, token,
            json={"records": [{"fields": s} for s in batch]})
        if err or not d or d.get("code") != 0:
            print(f"  [历史写入失败] {err or d.get('msg')}")
        else:
            total_ok += len(batch)
    print(f"✅ 历史快照写入 {total_ok}/{len(snapshots)} 条")

def get_job_open_dates(token):
    """从表1读取岗位开启日期和目标完成日期，用于计算时间进度"""
    records = get_records(token, TABLE_ID_JOB)
    dates = {}
    for rec in records:
        f = rec["fields"]
        name = f.get("岗位名称")
        if isinstance(name, list):
            name = name[0].get("text", "") if name else ""
        elif not isinstance(name, str):
            name = ""
        if not name: continue
        dates[name] = {
            "岗位开启日期_ms":  f.get("岗位开启日期"),
            "目标完成日期_ms":  f.get("目标完成日期"),
        }
    return dates
