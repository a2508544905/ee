"""异常用电检测 — 负值 / 过高用电 / 环比暴涨"""

# 单月用电量超过该值视为“过高用电”（度）
EXCESSIVE_USAGE_THRESHOLD = 5000.0
# 环比增长超过该倍数视为“暴涨”
SURGE_FACTOR = 2.0


def detect(records):
    """对历史记录做异常检测，返回异常条目列表。

    Args:
        records: history.query() 返回的记录列表（含 username/region/month/usage）。

    Returns:
        list[dict]: 每条含 level("warn"/"error")、message、record。
    """
    alerts = []
    prev_map = {}  # (username, region) -> {month, usage}，用于环比比较

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

        # 2. 过高用电
        if usage > EXCESSIVE_USAGE_THRESHOLD:
            alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量过高 "
                                        f"({usage:.0f} 度，超过 "
                                        f"{EXCESSIVE_USAGE_THRESHOLD:.0f} 度)", rec))

        # 3. 环比暴涨（同用户同地区，月份递增）
        prev = prev_map.get(key)
        if prev and prev["month"] and month and month > prev["month"]:
            if prev["usage"] > 0 and usage > prev["usage"] * SURGE_FACTOR:
                alerts.append(_make("warn", f"用户 {username or '(匿名)'} 用电量环比暴涨 "
                                            f"(上月 {prev['usage']:.0f} 度 → 本月 "
                                            f"{usage:.0f} 度)", rec))

        # 更新该用户最近一条（取月份较新者）
        if prev is None or (month is not None and (prev["month"] or 0) <= month):
            prev_map[key] = {"month": month, "usage": usage}

    return alerts


def _make(level, message, record):
    """构造一条异常记录。"""
    return {"level": level, "message": message, "record": record}