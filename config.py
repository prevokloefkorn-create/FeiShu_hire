# 飞书应用配置
APP_ID     = "cli_aaa38cd208789bb4"
APP_SECRET = "WhRA4vz5dcZ7k81Gh1T5xfoZXtRCBJyB"

# 多维表格
APP_TOKEN        = "F8FabYLgHa3G0As9fxtczoHNnfd"
TABLE_ID_JOB     = "tbl1QZufRcSjbjfw"   # 表1 招聘需求表
TABLE_ID_LOG     = "tblxJrhg7AnnQIh3"   # 表2 招聘进展记录表
TABLE_ID_CAND    = "tbl9YJbH6o9zGpsQ"   # 表3 候选人明细表
TABLE_ID_BOARD   = "tblpTDdNS15G8XrH"   # 表4 岗位健康度管理看板
TABLE_ID_ALERT   = "tblG35li6nCkz3Mt"   # 表5 预警推送记录表

# 兼容旧字段（同步脚本用）
TABLE_ID         = TABLE_ID_BOARD
HISTORY_TABLE_ID = TABLE_ID_LOG

# Webhook（部门群）
DEPT_WEBHOOKS = {
    "市场部": "https://open.feishu.cn/open-apis/bot/v2/hook/1ebe0533-3e91-4583-9bb0-3767d4ad4a07",
    # 待补充：
    # "研发部": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    # "销售部": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    # "产品部": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    # "HR部":   "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    # "财务部": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
}

# 总群webhook
DEFAULT_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/634fd9df-b7dd-4838-8d49-a4152e679ff9"

# 飞书API基础地址
BASE = "https://open.feishu.cn/open-apis"

# 阶段顺序
STAGE_ORDER = ["筛选", "评估", "面试", "Offer", "待入职", "已入职"]

# 健康度权重
HEALTH_WEIGHT = {"预警": 3, "关注": 2, "正常": 1}

# 差异化预警默认阈值（表1里没填时用这个）
PRIORITY_THRESHOLDS = {
    "P0": {"warn_days": 7,  "watch_days_low": 4,  "watch_days_high": 7,  "normal_days": 3},
    "P1": {"warn_days": 14, "watch_days_low": 8,  "watch_days_high": 14, "normal_days": 7},
    "P2": {"warn_days": 21, "watch_days_low": 14, "watch_days_high": 21, "normal_days": 14},
}
DEFAULT_THRESHOLD = PRIORITY_THRESHOLDS["P1"]

# 稳定性参数
BATCH_SIZE  = 10
BATCH_SLEEP = 0.5
MAX_RETRY   = 3
