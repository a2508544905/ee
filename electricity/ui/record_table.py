"""数据表格区：用 Treeview 展示所有已录入记录"""

import tkinter as tk
from tkinter import ttk

# 表格列定义：(列标识, 标题, 宽度)
COLUMNS = [
    ("username", "用户名", 100),
    ("month", "月份", 60),
    ("region", "地区", 100),
    ("usage", "用电量(度)", 100),
    ("total", "总电费(元)", 110),
    ("created_at", "记录时间", 150),
]


class RecordTable(ttk.LabelFrame):
    """展示历史记录的 Treeview 表格。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, text="已录入记录", padding=8, **kwargs)

        self.tree = ttk.Treeview(
            self, columns=[c[0] for c in COLUMNS], show="headings", height=10,
        )
        for key, title, width in COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    @staticmethod
    def _fmt_usage(value):
        """用电量格式化：整数显示为整数，小数保留原样。"""
        try:
            v = float(value)
            if v == int(v):
                return str(int(v))
            return f"{v:.2f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return value or ""

    def load(self, records):
        """用记录列表整体重灌表格。

        Args:
            records: history.query() 返回的记录列表
        """
        self.tree.delete(*self.tree.get_children())
        for rec in records:
            self.tree.insert(
                "",
                "end",
                values=(
                    rec.get("username") or "",
                    rec.get("month") or "",
                    rec.get("region") or "",
                    self._fmt_usage(rec.get("usage")),
                    f"{rec.get('total', 0):.2f}",
                    rec.get("created_at") or "",
                ),
            )

    def prepend(self, rec):
        """在表格顶部插入一条新记录。"""
        self.tree.insert(
            "",
            0,
            values=(
                rec.get("username") or "",
                rec.get("month") or "",
                rec.get("region") or "",
                self._fmt_usage(rec.get("usage")),
                f"{rec.get('total', 0):.2f}",
                rec.get("created_at") or "",
            ),
        )