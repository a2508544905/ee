"""记录导入 — 从 CSV 文件批量读取用电记录"""

import csv

# 期望的列顺序，兼容带/不带表头的文件
_COLUMN_MAP = {
    "username": "username",
    "用户": "username",
    "用户名": "username",
    "month": "month",
    "月份": "month",
    "region": "region",
    "地区": "region",
    "usage": "usage",
    "用电量": "usage",
    "用电量度": "usage",
}


def _normalize_header(header):
    """把表头行映射为标准列名；空表头按位置推断。"""
    normalized = []
    for h in header:
        key = (h or "").strip().lower()
        if key in _COLUMN_MAP:
            normalized.append(_COLUMN_MAP[key])
        else:
            normalized.append(key)  # 无法识别则原样保留，后续跳过
    return normalized


def read_records(path, default_region=None):
    """从 CSV 读取用电记录列表。

    支持：带表头（用户/月份/地区/用电量）或纯数据行（每行 2-4 列）。
    返回记录 dict 列表，仅包含能解析出 usage 的行。

    Raises:
        ValueError: 文件不存在、空文件或没有任何可用数据时。
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        raw_rows = [row for row in reader if any(cell.strip() for cell in row)]

    if not raw_rows:
        raise ValueError("文件为空或有内容但无有效行")

    # 判断首行是否为表头：首行含中文列名则按表头解析
    first = [c.strip() for c in raw_rows[0]]
    has_header = any(
        any(w in h for w in ("用户", "月份", "地区", "用电量", "usage", "month"))
        for h in first if h
    )

    if has_header:
        header = _normalize_header(first)
        data_rows = raw_rows[1:]
    else:
        header = ["username", "month", "region", "usage"]  # 无表头按位置
        data_rows = raw_rows

    records = []
    for row in data_rows:
        parsed = {}
        for col, cell in zip(header, row):
            parsed[col] = cell.strip()
        # 提取用电量（必须）
        usage = _parse_usage(parsed.get("usage") or parsed.get("用电量"))
        if usage is None:
            continue
        region = parsed.get("region") or default_region
        if not region:
            continue
        records.append({
            "username": parsed.get("username") or "",
            "month": _parse_month(parsed.get("month")),
            "region": region,
            "usage": usage,
        })

    if not records:
        raise ValueError("未解析到任何有效用电记录（需包含用电量列）")
    return records


def _parse_usage(value):
    """解析用电量，失败返回 None。"""
    if not value:
        return None
    try:
        v = float(value)
        if v < 0:
            return None
        return v
    except (TypeError, ValueError):
        return None


def _parse_month(value):
    """解析月份，非法返回 None。"""
    if not value:
        return None
    try:
        m = int(value)
        return m if 1 <= m <= 12 else None
    except (TypeError, ValueError):
        return None