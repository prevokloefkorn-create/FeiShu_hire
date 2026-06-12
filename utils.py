import time
import requests
from datetime import datetime, timezone
from config import APP_ID, APP_SECRET, BASE, MAX_RETRY

def get_token():
    r = requests.post(f"{BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=20).json()
    tok = r.get("tenant_access_token")
    if not tok:
        print(f"[换token失败] {r}")
        raise Exception("换token失败")
    return tok

def req_with_retry(method, url, token, max_retry=MAX_RETRY, **kw):
    headers = kw.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Content-Type", "application/json")
    for attempt in range(max_retry):
        try:
            time.sleep(0.1)
            r = requests.request(method, url, headers=headers, timeout=20, **kw)
            data = r.json()
            if data.get("code") not in (0, None):
                print(f"  [飞书报错] code={data.get('code')} msg={data.get('msg')}")
            return data, None
        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            print(f"  [超时] 第{attempt+1}次，{wait}秒后重试...")
            time.sleep(wait)
        except Exception as e:
            print(f"  [异常] {e}")
            time.sleep(1)
    return None, "max_retry_exceeded"

def cell_val(v):
    if v is None: return ""
    if isinstance(v, list): return v[0].get("text", "") if v and isinstance(v[0], dict) else ""
    if isinstance(v, dict): return v.get("text", str(v))
    return str(v)

def cell_num(fields, key):
    v = fields.get(key)
    if isinstance(v, (int, float)): return int(v)
    s = cell_val(v).strip()
    if s == "": return 0
    try: return int(float(s))
    except: return 0

def cell_date_days(fields, key):
    v = fields.get(key)
    if v is None: return None
    try:
        ms = int(v)
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except: return None
