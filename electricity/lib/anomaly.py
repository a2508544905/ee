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
    params = _resolve_thresholds(thresholds, excessive, surge, plunge, mean_factor)
    if params is None:
        return []

    alerts = []
    mean_map = _collect_usage_history(records)
    prev_map = {}   # (username, region) -> {month, usage}，用于环比

    for rec in records:
        usage = rec.get("usage") or 0
        username = rec.get("username") or ""
        region = rec.get("region") or ""
        month = rec.get("month") or None
        key = (username, region)
        prev = prev_map.get(key)

        # 1. 负值（异常）
        if usage < 0:
            alerts.append(_make("error",
                                f"用户 {username or '(匿名)'} 用电量为负值 ({usage} 度)，数据异常",
                                rec))
            continue

        # 2. 过高用电（绝对阈值）
        if usage > params["excessive"]:
            alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量过高 "
                                        f"({usage:.0f} 度，超过 {params['excessive']:.0f} 度)", rec))

        # 3. 环比暴涨 / 暴跌
        if _is_cyclical(prev, month):
            alert = _check_cycle(prev, usage, username, rec, params)
            if alert:
                alerts.append(alert)

        # 4. 远超该用户历史均值（排除当前条，避免自比）
        mean_alert = _check_mean_anomaly(mean_map, key, usage, username, rec, params)
        if mean_alert:
            alerts.append(mean_alert)

        # 更新最近一条用于下次环比
        if prev is None or (month is not None and (prev.get("month") or 0) <= month):
            prev_map[key] = {"month": month, "usage": usage}

    return alerts


def _resolve_thresholds(thresholds, excessive, surge, plunge, mean_factor):
    """解析最终阈值；任一参数非法（非数字）时返回 None 表示跳过检测。

    Args:
        thresholds: 配置缺省阈值字典。
        excessive/surge/plunge/mean_factor: 调用方传入的可覆盖值（可为 None）。

    Returns:
        dict | None: 解析后的阈值字典；任一值无法转数字时返回 None。
    """
    params = {
        "excessive": excessive if excessive is not None else thresholds["excessive_usage_threshold"],
        "surge": surge if surge is not None else thresholds["surge_factor"],
        "plunge": plunge if plunge is not None else thresholds["plunge_factor"],
        "mean_factor": mean_factor if mean_factor is not None else thresholds["mean_anomaly_factor"],
    }
    try:
        for key in params:
            params[key] = float(params[key])
    except (TypeError, ValueError):
        return None
    return params


def _collect_usage_history(records):
    """收集每个用户（用户名+地区）的正用量历史列表，用于计算均值。

    Args:
        records: 记录列表。

    Returns:
        dict: key=(username, region)，value=非负用量列表。
    """
    mean_map = {}
    for rec in records:
        usage = rec.get("usage") or 0
        if usage >= 0:
            key = (rec.get("username") or "", rec.get("region") or "")
            mean_map.setdefault(key, []).append(usage)
    return mean_map


def _is_cyclical(prev, month):
    """判断当前记录是否可与上条做环比：上月存在且月份递增。"""
    return bool(prev and prev.get("month") and month and prev["month"] < month)


def _check_cycle(prev, usage, username, rec, params):
    """检测环比暴涨/暴跌，命中时返回一条告警，否则返回 None。"""
    prev_usage = prev["usage"]
    if prev_usage <= 0:
        return None
    if usage > prev_usage * params["surge"]:
        return _make("warn", f"用户 {username or '(匿名)'} 用电量环比暴涨 "
                             f"(上月 {prev_usage:.0f} 度 → 本月 {usage:.0f} 度)", rec)
    if usage < prev_usage * params["plunge"]:
        return _make("warn", f"用户 {username or '(匿名)'} 用电量环比骤降 "
                             f"(上月 {prev_usage:.0f} 度 → 本月 {usage:.0f} 度)", rec)
    return None


def _check_mean_anomaly(mean_map, key, usage, username, rec, params):
    """检测单月用量是否远超该用户历史均值（排除当前条），命中返回告警。"""
    his_usages = mean_map.get(key, [])
    other_sum = sum(his_usages) - usage
    other_count = len(his_usages) - 1
    if other_count < 1:
        return None
    avg = other_sum / other_count
    if avg > 0 and usage > avg * params["mean_factor"]:
        return _make("warn", f"用户 {username or '(匿名)'} 用电量远超历史均值 "
                             f"(历史平均 {avg:.0f} 度，本月 {usage:.0f} 度，"
                             f"超 {params['mean_factor']:.0f} 倍)", rec)
    return None


def _make(level, message, record):
    """构造一条异常记录。"""
    return {"level": level, "message": message, "record": record}