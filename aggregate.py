#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from config import STAGE_ORDER

SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000

def calc_completion_rate(已入职数, 计划招聘人数):
    """完成率 = 已入职数 / 计划招聘人数"""
    if not 计划招聘人数 or 计划招聘人数 == 0:
        return 0
    return round(已入职数 / 计划招聘人数 * 100, 1)

def calc_time_progress(开启日期_ms, 目标完成日期_ms):
    """时间进度 = 已过天数 / 总天数"""
    if not 开启日期_ms or not 目标完成日期_ms:
        return 0
    try:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        total = int(目标完成日期_ms) - int(开启日期_ms)
        passed = now_ms - int(开启日期_ms)
        if total <= 0: return 100
        progress = round(passed / total * 100, 1)
        return min(progress, 100)
    except: return 0

def aggregate_candidates(records):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    seven_days_ago = now_ms - SEVEN_DAYS_MS
    result = {}

    for rec in records:
        f = rec["fields"]
        job_name = None
        v = f.get("应聘岗位")
        if isinstance(v, list): job_name = v[0].get("text", "") if v else ""
        elif isinstance(v, str): job_name = v
        if not job_name: continue

        status = f.get("候选人状态", "")
        if isinstance(status, list): status = status[0].get("text", "") if status else ""
        if status in ("已淘汰", "已放弃"): continue

        stage = f.get("当前阶段", "筛选")
        if isinstance(stage, list): stage = stage[0].get("text", "") if stage else "筛选"
        enter_time = f.get("进入当前阶段时间")

        if job_name not in result:
            result[job_name] = {s: 0 for s in STAGE_ORDER}
            result[job_name]["近7天新增简历"] = 0
            result[job_name]["该阶段停留天数"] = 0
            result[job_name]["_max_stay_days"] = 0

        if stage in result[job_name]:
            result[job_name][stage] += 1

        if stage == "筛选" and enter_time:
            try:
                if int(enter_time) >= seven_days_ago:
                    result[job_name]["近7天新增简历"] += 1
            except: pass

        if enter_time:
            try:
                stay_days = int((now_ms - int(enter_time)) / (24*60*60*1000))
                if stay_days > result[job_name]["_max_stay_days"]:
                    result[job_name]["_max_stay_days"] = stay_days
                    result[job_name]["该阶段停留天数"] = stay_days
            except: pass

    for job_name, data in result.items():
        data["在投简历数"] = (data["筛选"] + data["评估"] +
                            data["面试"] + data["Offer"])
        del data["_max_stay_days"]

    return result
