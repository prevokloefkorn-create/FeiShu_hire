from config import STAGE_ORDER, HEALTH_WEIGHT, PRIORITY_THRESHOLDS, DEFAULT_THRESHOLD
from utils import cell_num, cell_val, cell_date_days

def calc_main_stage(fields):
    for stage in reversed(STAGE_ORDER):
        if cell_num(fields, stage) > 0:
            return stage
    return "筛选"

def calc_health(fields, job_config=None):
    """
    fields: 看板表里的字段
    job_config: 从表1读取的该岗位配置（含自定义阈值）
    """
    cv7      = cell_num(fields, "近7天新增简历")
    days     = cell_num(fields, "该阶段停留天数")
    筛选      = cell_num(fields, "筛选")
    评估      = cell_num(fields, "评估")
    offer    = cell_num(fields, "Offer")
    已入职    = cell_num(fields, "已入职")
    在投      = cell_num(fields, "在投简历数")
    开启天数  = cell_date_days(fields, "岗位开启日期")
    priority = cell_val(fields.get("岗位优先级")).strip() or "P1"

    # 优先用表1的自定义阈值，没有就用优先级默认值
    thr = PRIORITY_THRESHOLDS.get(priority, DEFAULT_THRESHOLD).copy()
    if job_config:
        custom_days = job_config.get("预警阈值-停留天数")
        custom_cv7  = job_config.get("预警阈值-7天简历数")
        if custom_days and custom_days > 0:
            thr["warn_days"]        = custom_days
            thr["watch_days_high"]  = int(custom_days * 0.7)
            thr["watch_days_low"]   = int(custom_days * 0.5)
        if custom_cv7 and custom_cv7 > 0:
            thr["warn_cv7"] = custom_cv7
    else:
        thr["warn_cv7"] = 0  # 默认近7天=0才预警

    results = []

    # R1 近7天简历数
    warn_cv7 = thr.get("warn_cv7", 0)
    if cv7 <= warn_cv7:
        results.append(("预警", f"7天简历≤{warn_cv7}份"))
    elif 0 < cv7 < 3:
        results.append(("关注", "简历偏少"))

    # R2 该阶段停留天数
    if days > thr["warn_days"]:
        results.append(("预警", f"停留{days}天"))
    elif thr["watch_days_low"] < days <= thr["watch_days_high"]:
        results.append(("关注", f"停留{days}天"))

    # R3 新岗位无人投递
    if 开启天数 is not None and 开启天数 <= 7 and 在投 == 0:
        results.append(("预警", "新岗位无人投递"))

    # R4 简历通过率为0
    if 筛选 >= 10 and 评估 == 0:
        results.append(("关注", "简历通过率为0"))

    # R5 长期无进展
    if 开启天数 is not None and 开启天数 > 30 and 已入职 == 0 and offer == 0:
        results.append(("关注", f"开启{开启天数}天未出offer"))

    if not results: return "正常", ""
    worst = max(results, key=lambda x: HEALTH_WEIGHT.get(x[0], 0))[0]
    reasons = [r for h, r in results if h == worst]
    return worst, "；".join(reasons)
