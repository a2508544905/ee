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

# 批量导入尝试的编码顺序：UTF-8-sig（兼容 BOM）→ GBK（国内常见）→ UTF-8
_DETECT_ENCODINGS = ("utf-8-sig", "gbk", "utf-8")

# 单月用电量硬上限（度）：与 validator.MAX_USAGE 保持一致，超限视为录入错误
MAX_USAGE = 100000.0

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
    """解析用电量，非法、为负或超出上限返回 None。"""
    if not value:
        return None
    try:
        v = float(value)
        if v < 0 or v > MAX_USAGE:
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


def _read_text(path):
    """以自动检测的编码读取整个文件文本。

    依次尝试 UTF-8-sig / GBK / UTF-8，全部失败时抛出带中文提示的异常。

    Args:
        path: CSV 文件路径。

    Returns:
        str: 文件文本内容。

    Raises:
        ValueError: 文件不存在或无法用已知编码解码时。
    """
    if not os.path.isfile(path):
        raise ValueError(f"文件不存在：{path}")
    last_exc = None
    for encoding in _DETECT_ENCODINGS:
        try:
            with open(path, "r", encoding=encoding, newline="") as f:
                return f.read()
        except UnicodeDecodeError as exc:
            last_exc = exc
    raise ValueError(f"无法识别文件编码，请使用 UTF-8 或 GBK 编码：{path}（{last_exc}）")


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
        import io
        text = _read_text(path)
        raw_rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]

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
        errors = []          # 记录被跳过的行及原因
        duplicates = []      # 记录重复（同用户同月份）的行
        seen_keys = set()    # 已出现过的 (username, month)

        for row in data_rows:
            parsed = {}
            for col, cell in zip(header, row):
                parsed[col] = cell.strip()

            raw_usage = parsed.get("usage") or parsed.get("用电量")
            usage = _parse_usage(raw_usage)
            if usage is None:
                errors.append(f"第{len(errors) + len(records) + len(duplicates) + 2}行：用电量无效（{raw_usage or '空'}）")
                continue

            region = parsed.get("region") or default_region
            if not region:
                errors.append("地区缺失，已跳过")
                continue

            raw_month = parsed.get("month")
            month = _parse_month(raw_month)
            if month is None:
                errors.append(f"月份无效（{raw_month or '空'}），已跳过")
                continue

            username = parsed.get("username") or ""
            if (username, month) in seen_keys:
                duplicates.append(f"{username or '(空)'} 第{month}月")
                continue
            seen_keys.add((username, month))

            try:
                records.append(self._build_record(username, month, region, usage))
            except ValueError as exc:
                errors.append(f"{username}：{exc}")

        self.last_report = {
            "loaded": len(records),
            "skipped": len(errors),
            "errors": errors,
            "duplicates": duplicates,
        }

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