"""异常用电检测 — 负值 / 过高用电 / 环比暴涨与暴跌 / 远超历史均值

检测规则阈值从 config/anomaly.json 读取（可用 detect() 的 kwargs 覆盖）：
  - negative:        用电量为负值
  - excessive:       单月用电量超过绝对上限
  - surge:           环比上月增长倍数超过阈值
  - plunge:          环比上月下降，用量不足上月该比例（视为暴跌）
  - mean_anomaly:    远超该用户自身历史均值的倍数
"""

import json
import os

# 配置文件路径与缺省阈值
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "anomaly.json")
DEFAULTS = {
    "excessive_usage_threshold": 5000.0,
    "surge_factor": 2.0,
    "plunge_factor": 0.2,
    "mean_anomaly_factor": 3.0,
}

_loaded = None


def _load_thresholds():
    """读取异常阈值配置；文件缺失或损坏时回退到缺省值。"""
    global _loaded
    if _loaded is not None:
        return _loaded
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in DEFAULTS:
            if key in data:
                cfg[key] = float(data[key])
    except (OSError, ValueError, TypeError):
        pass
    _loaded = cfg
    return _loaded


def detect(records, excessive=None, surge=None, plunge=None, mean_factor=None):
    """对历史记录做异常检测，返回异常条目列表。

    Args:
        records: history.query() 返回的记录列表（含 username/region/month/usage）。
        excessive: 覆盖超高用电绝对阈值；surge/plunge/mean_factor 同理可覆盖。

    Returns:
        list[dict]: 每条含 level("warn"/"error")、message、record。
    """
    thresholds = _load_thresholds()
    excessive = excessive if excessive is not None else thresholds["excessive_usage_threshold"]
    surge = surge if surge is not None else thresholds["surge_factor"]
    plunge = plunge if plunge is not None else thresholds["plunge_factor"]
    mean_factor = mean_factor if mean_factor is not None else thresholds["mean_anomaly_factor"]

    try:
        excessive = float(excessive)
        surge = float(surge)
        plunge = float(plunge)
        mean_factor = float(mean_factor)
    except (TypeError, ValueError):
        return []

    alerts = []
    prev_map = {}   # (username, region) -> {month, usage}，用于环比与均值
    mean_map = {}   # (username, region) -> [usage...]，用于算历史均值

    # 第一遍：收集每个用户的历史用量，便于算均值
    for rec in records:
        usage = rec.get("usage") or 0
        username = rec.get("username") or ""
        region = rec.get("region") or ""
        key = (username, region)
        if usage >= 0:
            mean_map.setdefault(key, []).append(usage)

    for rec in records:
        usage = rec.get("usage") or 0
        username = rec.get("username") or ""
        region = rec.get("region") or ""
        month = rec.get("month") or None
        key = (username, region)

        # 1. 负值（异常）
        if usage < 0:
            alerts.append(_make("error", f"用户 {username or '(匿名)'} 用电量为负值 "
                                          f"({usage} 度)，数据异常", rec))
            continue

        # 2. 过高用电（绝对阈值）
        if usage > excessive:
            alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量过高 "
                                        f"({usage:.0f} 度，超过 {excessive:.0f} 度)", rec))

        # 3. 环比暴涨 / 暴跌（同用户同地区，月份递增）
        prev = prev_map.get(key)
        if prev and prev["month"] and month and prev["month"] < month:
            if prev["usage"] > 0 and usage > prev["usage"] * surge:
                alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量环比暴涨 "
                                            f"(上月 {prev['usage']:.0f} 度 → 本月 "
                                            f"{usage:.0f} 度)", rec))
            elif prev["usage"] > 0 and usage < prev["usage"] * plunge:
                alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量环比骤降 "
                                            f"(上月 {prev['usage']:.0f} 度 → 本月 "
                                            f"{usage:.0f} 度)", rec))

        # 4. 远超该用户历史均值（排除当前条，避免自比）
        his_usages = [u for u in mean_map.get(key, [])]
        other = sum(his_usages) - usage
        count = len(his_usages) - 1
        if count >= 1:
            avg = other / count
            if avg > 0 and usage > avg * mean_factor:
                alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量远超历史均值 "
                                            f"(历史平均 {avg:.0f} 度，本月 {usage:.0f} 度，"
                                            f"超 {mean_factor:.0f} 倍)", rec))

        # 更新最近一条
        if prev is None or (month is not None and (prev.get("month") or 0) <= month):
            prev_map[key] = {"month": month, "usage": usage}

    return alerts


def _make(level, message, record):
    """构造一条异常记录。"""
    return {"level": level, "message": message, "record": record}