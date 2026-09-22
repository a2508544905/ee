"""报表导出 — 将记录导出为 CSV 或 Excel(.xlsx)，Excel 含多 Sheet 汇总

职责：
  - export_csv: 导出原始数据为 CSV（含表头，金额保留两位小数）
  - export_excel: 导出 Excel，含两个 Sheet：
      * 「原始数据」：用户名 | 月份 | 用电量(度) | 电费(元)
      * 「用户汇总」：用户名 | 总用电量 | 总电费 | 平均月电费
      每列宽度按内容自动调整。

用法：
    from lib.report_exporter import export_csv, export_excel
    export_csv(records, "out.csv")
    export_excel(records, "out.xlsx")
"""

import csv
import os

from lib import statistics


def _raw_rows(records):
    """把记录列表整理为按月份升序的原始数据行列表（含表头，金额保留 2 位）。"""
    sorted_recs = sorted(records, key=lambda r: (str(r.get("username") or ""), r.get("month") or 0))
    rows = [["用户名", "月份", "用电量(度)", "电费(元)"]]
    for r in sorted_recs:
        rows.append([
            r.get("username") or "",
            r.get("month") or "",
            round(r.get("usage") or 0, 2),
            round(r.get("total") or 0, 2),
        ])
    return rows


def export_csv(records, file_path):
    """将记录导出为 CSV（UTF-8 with BOM，表头 + 金额 2 位小数）。"""
    rows = _raw_rows(records)
    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    return len(rows) - 1


def _user_summary_rows(records):
    """统计每个用户的总用电量、总电费、平均月电费，返回带表头行列表。"""
    rows = [["用户名", "总用电量", "总电费", "平均月电费"]]
    for u in statistics.group_by_user(records):
        rows.append([
            u["username"],
            round(u["total_usage"], 2),
            round(u["total_fee"], 2),
            round(u["avg_fee"], 2),
        ])
    return rows


def export_excel(records, file_path):
    """导出 Excel：Sheet1 原始数据，Sheet2 用户汇总；列宽按内容自适应。

    Raises:
        RuntimeError: 未安装 openpyxl 时。
        ValueError: 文件扩展名不是 .xlsx 时。
    """
    if os.path.splitext(file_path)[1].lower() != ".xlsx":
        raise ValueError("Excel 导出请使用 .xlsx 扩展名")
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("未安装 openpyxl，无法导出 Excel。请先 pip install openpyxl") from exc

    wb = Workbook()
    _fill_sheet(wb.active, "原始数据", _raw_rows(records))

    us = wb.create_sheet("用户汇总")
    _fill_sheet(us, "用户汇总", _user_summary_rows(records))

    wb.save(file_path)
    return len(_raw_rows(records)) - 1


def _fill_sheet(ws, title, rows):
    """把行数据写入工作表并根据内容自适应列宽。"""
    from openpyxl.utils import get_column_letter
    ws.title = title
    for row in rows:
        ws.append(row)
    # 列宽自适应：按每列最大单元格长度（中文按 2 倍宽度估算）
    for col_idx in range(1, len(rows[0]) + 1):
        max_len = 0
        for r in rows:
            val = r[col_idx - 1] if len(r) >= col_idx else ""
            width = sum(2 if ord(ch) > 127 else 1 for ch in str(val))
            max_len = max(max_len, width)
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 2


def export(records, file_path):
    """按文件扩展名自动选择导出格式。

    Returns:
        导出的记录条数。

    Raises:
        ValueError: 文件扩展名不是 .csv / .xlsx 时。
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return export_csv(records, file_path)
    if ext == ".xlsx":
        return export_excel(records, file_path)
    raise ValueError("不支持的导出格式，请使用 .csv 或 .xlsx")