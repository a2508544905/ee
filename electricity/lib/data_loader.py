"""数据加载与管理 — CSV 批量导入、单条录入、JSON 持久化、电费自动计算

职责：
  - 从 CSV 批量读取用电记录，逐条调用计算器计算电费，返回完整记录列表
  - 实现单条录入（输入用户名/月份/用电量，自动计算电费）
  - 将记录以 JSON 持久化到 data/records.json（中文可读、损坏容错）

用法：
    loader = DataLoader(calculator, tariff_manager)
    records = loader.load_csv("data/sample.csv")      # 批量导入
    loader.save_records(records)                      # 保存
    records = loader.load_records()                   # 加载
"""

import csv
import json
import os

# JSON 持久化文件路径
DEFAULT_RECORDS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "records.json")

# CSV 列名映射，兼容中英文表头
_COLUMN_MAP = {
    "username": "username", "用户": "username", "用户名": "username",
    "month": "month", "月份": "month",
    "region": "region", "地区": "region",
    "usage": "usage", "用电量": "usage", "用电量度": "usage", "用电量(度)": "usage",
}


def _normalize_header(header):
    """把表头行映射为统一列名，无法识别的列名原样保留。"""
    return [_COLUMN_MAP.get(h, h) for h in header]


def _parse_usage(value):
    """解析用电量，非法或为负返回 None。"""
    if not value:
        return None
    try:
        v = float(value)
        return v if v >= 0 else None
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


class DataLoader:
    """CSV 导入、单条录入与 JSON 持久化的统一入口。"""

    def __init__(self, calculator, records_path=None):
        """注入计算器对象，便于逐条计算电费。"""
        self.calculator = calculator
        self.records_path = records_path or os.path.normpath(DEFAULT_RECORDS_PATH)

    # ── 批量导入 ──
    def load_csv(self, path, default_region=None):
        """从 CSV 批量读取记录，逐条计算电费后返回完整记录列表。

        支持带表头（用户名/月份/地区/用电量）或纯数据行（每行 2-4 列）。

        Returns:
            list[dict]: 每条含 username/month/region/usage/total/tiers/current_tier。

        Raises:
            ValueError: 文件为空、无有效行、或没有任何可用数据时。
        """
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            raw_rows = [row for row in csv.reader(f) if any(cell.strip() for cell in row)]

        if not raw_rows:
            raise ValueError("文件为空或有内容但无有效行")

        first = [c.strip() for c in raw_rows[0]]
        has_header = any(
            any(w in h for w in ("用户", "月份", "地区", "用电量", "usage", "month"))
            for h in first if h
        )

        header = _normalize_header(first) if has_header else ["username", "month", "region", "usage"]
        data_rows = raw_rows[1:] if has_header else raw_rows

        records = []
        for row in data_rows:
            parsed = {}
            for col, cell in zip(header, row):
                parsed[col] = cell.strip()
            usage = _parse_usage(parsed.get("usage") or parsed.get("用电量"))
            if usage is None:
                continue
            region = parsed.get("region") or default_region
            if not region:
                continue
            records.append(self._build_record(
                parsed.get("username") or "",
                _parse_month(parsed.get("month")),
                region,
                usage,
            ))

        if not records:
            raise ValueError("未解析到任何有效用电记录（需包含用电量列）")
        return records

    # ── 单条录入 ──
    def add_record(self, username, month, region, usage):
        """录入单条记录，自动计算电费。

        Args:
            username: 用户名（标签，可为空）。
            month: 月份（1-12，可为空）。
            region: 地区名。
            usage: 用电量（度，≥0）。

        Returns:
            dict: 完整记录（含 total/tiers/current_tier）。

        Raises:
            ValueError: 用电量为负数时。
        """
        return self._build_record(username, month, region, usage)

    def _build_record(self, username, month, region, usage):
        """构造记录字典并调用计算器计算电费（负数用电量报错）。"""
        if usage is None or usage < 0:
            raise ValueError("用电量不能为负数")
        result = self.calculator.calculate(region, usage)
        return {
            "username": username or "",
            "month": month,
            "region": region,
            "usage": usage,
            "total": result["total"],
            "tiers": result["tiers"],
            "current_tier": result["current_tier"],
        }

    # ── JSON 持久化 ──
    def save_records(self, records):
        """把记录列表序列化为 JSON 写入文件（中文可读、缩进 2）。"""
        os.makedirs(os.path.dirname(self.records_path), exist_ok=True)
        with open(self.records_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def load_records(self):
        """从 JSON 反序列化读取记录；文件不存在或损坏时返回空列表。"""
        if not os.path.isfile(self.records_path):
            return []
        try:
            with open(self.records_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []