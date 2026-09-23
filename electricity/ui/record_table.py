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
    """展示历史记录的 Treeview 表格，支持选中删除。"""

    def __init__(self, master, on_delete_selected=None, **kwargs):
        super().__init__(master, text="已录入记录", padding=8, **kwargs)

        self.on_delete_selected = on_delete_selected  # 删除选中行回调(由主窗口注入)
        self._selected_id = None   # 当前选中行的记录 id

        # 顶部工具条：删除选中按钮
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 4))
        self.del_btn = ttk.Button(
            toolbar, text="删除选中记录", command=self._delete_selected, state="disabled",
        )
        self.del_btn.pack(side="left")

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

        # 选中变化时启用/禁用删除按钮
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        # 支持右键删除与 Delete 键删除
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected())

    def _on_select(self, _event):
        """表格选中变化：启用删除按钮并记录选中 id。"""
        sel = self.tree.selection()
        if sel:
            self._selected_id = self._iid_to_id(sel[0])
            self.del_btn.config(state="normal")
        else:
            self._selected_id = None
            self.del_btn.config(state="disabled")

    def _on_right_click(self, event):
        """右键行：选中该行并弹出删除菜单。"""
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self._on_select(None)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="删除该记录", command=self._delete_selected)
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _iid_to_id(self, iid):
        """把 Treeview 行 iid 还原为记录 id。"""
        try:
            return int(iid)
        except (TypeError, ValueError):
            return None

    def _delete_selected(self):
        """触发删除当前选中记录的回调（回调由主窗口实现）。"""
        if self._selected_id is not None and self.on_delete_selected:
            self.on_delete_selected(self._selected_id)

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
            records: history.query() 返回的记录列表（必需含 id）
        """
        self.tree.delete(*self.tree.get_children())
        for rec in records:
            iid = rec.get("id")
            if iid is None:
                iid = self._next_iid()   # 兜底：缺 id 时生成一个负临时 id
            self.tree.insert(
                "", "end", iid=str(iid),
                values=(
                    rec.get("username") or "",
                    rec.get("month") or "",
                    rec.get("region") or "",
                    self._fmt_usage(rec.get("usage")),
                    f"{rec.get('total', 0):.2f}",
                    rec.get("created_at") or "",
                ),
            )
        self._selected_id = None
        self.del_btn.config(state="disabled")

    def _next_iid(self):
        """生成一个不与真实 id 冲突的负临时 iid。"""
        self._temp_iid = getattr(self, "_temp_iid", 0) - 1
        return self._temp_iid