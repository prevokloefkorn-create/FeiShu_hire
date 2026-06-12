import requests
from datetime import datetime
from config import DEFAULT_WEBHOOK

def notify_result(ok, fail, changed, duration, errors):
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    status = "✅ 同步正常" if fail == 0 else "⚠️ 同步有失败项"
    lines = [
        f"{status} · {today}",
        f"成功 {ok} 条 · 失败 {fail} 条 · 健康度变化 {changed} 条 · 耗时 {duration}秒",
    ]
    if errors:
        lines.append("失败明细：" + "、".join(errors[:5]))
    requests.post(DEFAULT_WEBHOOK, json={
        "msg_type": "text",
        "content": {"text": "\n".join(lines)}
    }, timeout=10)
