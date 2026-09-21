"""阶梯电价计算核心算法（纯算法，不依赖任何外部模块）"""


def calculate_tiered_bill(usage, tiers):
    """按阶梯档位分段计算电费。

    Args:
        usage: 用电量（度/kWh）
        tiers: 档位列表，如 [{"min": 0, "max": 260, "price": 0.59}, ...]

    Returns:
        list: 每档明细 [{"tier": 1, "usage": 260, "price": 0.59, "amount": 153.40}, ...]
        float: 总电费
    """
    if usage <= 0:
        return [], 0.0

    result = []
    total = 0.0

    for i, tier in enumerate(tiers):
        tier_min = tier["min"]
        tier_max = tier["max"]
        tier_price = tier["price"]

        if usage <= tier_min:
            break

        upper = usage if (tier_max is None or usage < tier_max) else tier_max
        tier_usage = upper - tier_min

        if tier_usage <= 0:
            continue

        amount = round(tier_usage * tier_price, 2)
        result.append({
            "tier": i + 1,
            "usage": tier_usage,
            "price": tier_price,
            "amount": amount,
        })
        total += amount

    return result, round(total, 2)


def get_current_tier(usage, tiers):
    """判断当前用电量落在哪个档位。

    Returns:
        int: 档位序号（从1开始），0表示未落入任何档
    """
    for i, tier in enumerate(tiers):
        tier_min = tier["min"]
        tier_max = tier["max"]
        if tier_max is None:
            if usage > tier_min:
                return i + 1
        elif tier_min < usage <= tier_max:
            return i + 1
    return 0


def get_distance_to_next_tier(usage, tiers):
    """计算距下一档的差距。

    Returns:
        dict: {"next_tier": 2, "remaining": 20, "price_diff": 0.05}
              如果已在最高档，next_tier 为 None
    """
    current = get_current_tier(usage, tiers)
    if current == 0 or current >= len(tiers):
        return {"next_tier": None, "remaining": 0, "price_diff": 0.0}

    current_tier = tiers[current - 1]
    next_tier = tiers[current]

    remaining = current_tier["max"] - usage
    price_diff = round(next_tier["price"] - current_tier["price"], 2)

    return {
        "next_tier": current + 1,
        "remaining": round(remaining, 2),
        "price_diff": price_diff,
    }


def estimate_usage_by_budget(budget, tiers):
    """根据预算金额反推可使用电量。

    Args:
        budget: 预算金额（元）
        tiers: 档位列表

    Returns:
        float: 可使用电量（度）
    """
    if budget <= 0:
        return 0.0

    remaining_budget = budget
    total_usage = 0.0

    for tier in tiers:
        tier_min = tier["min"]
        tier_max = tier["max"]
        tier_price = tier["price"]

        if tier_price <= 0:
            continue

        if tier_max is None:
            total_usage = tier_min + remaining_budget / tier_price
            break

        tier_capacity = tier_max - tier_min
        tier_cost = tier_capacity * tier_price

        if remaining_budget >= tier_cost:
            remaining_budget -= tier_cost
            total_usage = tier_max
        else:
            total_usage = tier_min + remaining_budget / tier_price
            remaining_budget = 0
            break

    return round(total_usage, 2)
