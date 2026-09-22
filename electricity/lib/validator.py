"""输入校验与错误处理 — 统一校验一次录入的全部字段"""

import math

# 单月用电量硬上限（度）：超过视为明显录入错误，直接拒绝
MAX_USAGE = 100000.0


def parse_usage(value_text):
    """解析并校验用电量输入。

    Args:
        value_text: 用电量原始输入（字符串或数字）。

    Returns:
        float: 合法用电量。

    Raises:
        ValueError: 为空、非数字、负数、过大或非有限数时抛出，附带中文提示。
    """
    if value_text is None or not str(value_text).strip():
        raise ValueError("请输入用电量")
    try:
        usage = float(value_text)
    except (TypeError, ValueError):
        raise ValueError("用电量必须是有效数字")
    if not math.isfinite(usage):
        raise ValueError("用电量必须是有效数字")
    if usage < 0:
        raise ValueError("用电量不能为负数")
    if usage > MAX_USAGE:
        raise ValueError(f"用电量过大，单月不能超过 {MAX_USAGE:.0f} 度")
    return usage


def parse_month(value_text):
    """解析并校验月份。

    Args:
        value_text: 月份原始输入；为空允许（返回 None）。

    Returns:
        int | None: 1-12 的整月，空返回 None。

    Raises:
        ValueError: 非 1-12 的月份时抛出。
    """
    if value_text is None or not str(value_text).strip():
        return None
    try:
        month = int(value_text)
    except (TypeError, ValueError):
        raise ValueError("月份必须是 1-12 的整数")
    if month < 1 or month > 12:
        raise ValueError("月份必须在 1-12 之间")
    return month


def validate_record(text_username, text_month, region, text_usage):
    """统一校验一次录入的全部字段，返回清洗后的记录数据。

    Args:
        text_username: 用户名（可为空字符串）。
        text_month: 月份输入（可为空）。
        region: 地区（下拉选中）。
        text_usage: 用电量输入。

    Returns:
        dict: {"username", "month", "region", "usage"}，字段已清洗。

    Raises:
        ValueError: 任一字段非法时抛出，附带对应中文提示。
    """
    if not region or not str(region).strip():
        raise ValueError("请选择地区")

    username = (text_username or "").strip()
    month = parse_month(text_month)
    usage = parse_usage(text_usage)

    return {
        "username": username,
        "month": month,
        "region": region,
        "usage": usage,
    }