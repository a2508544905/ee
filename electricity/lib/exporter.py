"""记录导出 — 将计算历史记录导出为 CSV 或 Excel(.xlsx)"""

import csv
import os


def _records_to_rows(records):
    """把记录字典列表转换为带表头的行列表。"""
    rows = [["用户名", "月份", "地区", "用电量(度)", "总电费(元)", "当前档位", "记录时间"]]
    for r in records:
        rows.append([
            r.get("username") or "",
            r.get("month") or "",
            r.get("region") or "",
            r.get("usage") or 0,
            r.get("total") or 0,
            r.get("current_tier") or "",
            r.get("created_at") or "",
        ])
    return rows


def export_csv(records, file_path):
    """将记录导出为 CSV（UTF-8 with BOM，Excel 可直接打开）。"""
    rows = _records_to_rows(records)
    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    return len(rows) - 1


def export_xlsx(records, file_path):
    """将记录导出为 Excel .xlsx（依赖 openpyxl）。"""
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("未安装 openpyxl，无法导出 Excel。请先 pip install openpyxl") from exc

    wb = Workbook()
    ws = wb.active
    ws.title = "电费记录"
    for row in _records_to_rows(records):
        ws.append(row)
    wb.save(file_path)
    return len(_records_to_rows(records)) - 1


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
        return export_xlsx(records, file_path)
    raise ValueError("不支持的导出格式，请使用 .csv 或 .xlsx")