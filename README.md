# 飞书招聘健康度看板

## 项目结构
- config.py      配置文件（webhook、表格ID等）
- utils.py       工具函数（token、字段解析、重试）
- health.py      健康度计算规则
- bitable.py     多维表格读写
- alert.py       分部门推送
- notify.py      运行监控推送
- sync.py        主同步脚本（入口）
- run.sh         定时任务运行脚本
- logs/          运行日志目录

## 运行方式
python3 sync.py

## 设置定时任务（每15分钟）
crontab -e
加入：*/15 * * * * /Users/apple/Documents/feishu_recruit/run.sh

## 待补充
- config.py 里的 DEPT_WEBHOOKS 补全其他5个部门
- HR开招聘后台权限后接入真实数据
