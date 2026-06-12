#!/bin/bash
# 定时任务运行脚本
cd ~/Documents/feishu_recruit
/usr/bin/python3 sync.py >> logs/sync.log 2>&1
