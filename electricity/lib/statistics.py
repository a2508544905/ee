"""统计汇总 — 对记录列表做多维度统计（纯函数，通过参数接收数据，低耦合）

约定：
  - 每个统计功能是独立函数，函数名以动词开头
  - 通过函数参数接收记录数据，不直接 import 数据加载模块内部变量
  - 返回数据（字典或列表），不在函数内部 print
"""


def calculate_total_fee(records):
    """计算所有记录的总电费（元）。

    Returns:
        float: 总电费。
    """
    return sum(r.get("total") or 0 for r in records)


def calculate_avg_fee(records):
    """计算所有记录的平均电费（元/条）。

    Returns:
        float: 平均电费；无记录时返回 0。
    """
    total = calculate_total_fee(records)
    return total / len(records) if records else 0.0


def get_usage_ranking(records, top=10):
    """按用电量从高到低排行（默认 Top 10）。

    Returns:
        list[dict]: 每条含 username/usage，按 usage 降序。
    """
    ranked = sorted(records, key=lambda r: r.get("usage") or 0, reverse=True)
    return [{"username": r.get("username") or "", "usage": r.get("usage") or 0}
            for r in ranked[:top]]


def group_by_user(records):
    """按用户汇总（每个用户的总用电量、总电费、平均月电费）。

    Returns:
        list[dict]: 每条含 username/total_usage/total_fee/avg_fee，按总用电量降序。
    """
    agg = {}
    for r in records:
        name = r.get("username") or ""
        agg.setdefault(name, {"username": name, "usage": 0.0, "fee": 0.0, "count": 0})
        agg[name]["usage"] += r.get("usage") or 0
        agg[name]["fee"] += r.get("total") or 0
        agg[name]["count"] += 1

    result = []
    for name, d in agg.items():
        result.append({
            "username": d["username"],
            "total_usage": d["usage"],
            "total_fee": d["fee"],
            "avg_fee": d["fee"] / d["count"] if d["count"] else 0.0,
        })
    result.sort(key=lambda x: x["total_usage"], reverse=True)
    return result


def group_by_month(records):
    """按月度汇总（每个月的总用电量、总电费）。

    Returns:
        list[dict]: 每条含 month/total_usage/total_fee，按月份升序。
    """
    agg = {}
    for r in records:
        m = r.get("month")
        if not m:
            continue
        agg.setdefault(m, {"month": m, "usage": 0.0, "fee": 0.0})
        agg[m]["usage"] += r.get("usage") or 0
        agg[m]["fee"] += r.get("total") or 0
    result = [
        {"month": d["month"], "total_usage": d["usage"], "total_fee": d["fee"]}
        for d in agg.values()
    ]
    result.sort(key=lambda x: x["month"])
    return result


def calculate_tier_ratio(records):
    """计算各档位用电量的占比分布。

    Returns:
        list[dict]: 每条含 tier/total_usage/ratio(0~1)，按档位升序。
    """
    agg = {}
    total_usage = 0.0
    for r in records:
        tier = r.get("current_tier") or None
        usage = r.get("usage") or 0
        total_usage += usage
        key = tier if tier is not None else "未知"
        agg.setdefault(key, {"tier": tier, "usage": 0.0})
        agg[key]["usage"] += usage

    result = [
        {"tier": d["tier"], "total_usage": d["usage"],
         "ratio": d["usage"] / total_usage if total_usage else 0.0}
        for d in agg.values()
    ]
    result.sort(key=lambda x: (x["tier"] is None, x["tier"] if x["tier"] is not None else 0))
    return result