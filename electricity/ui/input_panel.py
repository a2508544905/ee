"""输入区控件：用户名、月份下拉、用电量、计算按钮"""

import tkinter as tk
from tkinter import ttk


class InputPanel(ttk.LabelFrame):
    """顶部输入区。持有输入控件，通过 on_calculate 回调通知外部。"""

    def __init__(self, master, regions, on_calculate, default_region=None, users=None, **kwargs):
        super().__init__(master, text="输入", padding=12, **kwargs)

        self._on_calculate = on_calculate
        self._default_region = default_region

        # 用户名（从预置名单下拉选择，不手输）
        ttk.Label(self, text="用户：").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        self.user_combo = ttk.Combobox(
            self, textvariable=self.username_var, state="readonly", width=8,
        )
        self.user_combo.grid(row=0, column=1, padx=6)
        self.set_users(users or [])

        # 月份（下拉，1-12）
        ttk.Label(self, text="月份：").grid(row=0, column=2, sticky="w")
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(
            self, textvariable=self.month_var, state="readonly", width=6,
            values=[str(m) for m in range(1, 13)],
        )
        self.month_combo.grid(row=0, column=3, padx=6)

        # 地区（下拉）
        ttk.Label(self, text="地区：").grid(row=0, column=4, sticky="w")
        self.region_var = tk.StringVar()
        self.region_combo = ttk.Combobox(
            self, textvariable=self.region_var, state="readonly", width=10,
        )
        self.region_combo.grid(row=0, column=5, padx=6)
        self.set_regions(regions)

        # 用电量
        ttk.Label(self, text="用电量（度）：").grid(row=0, column=6, sticky="w")
        self.usage_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.usage_var, width=12).grid(row=0, column=7, padx=6)

        # 计算按钮
        ttk.Button(self, text="计算", command=self._on_calculate).grid(row=0, column=8, padx=10)

    def get_inputs(self):
        """收集并返回当前输入值（原始字符串，尚未校验）。"""
        return {
            "username": self.username_var.get().strip(),
            "month": self.month_var.get(),
            "region": self.region_var.get(),
            "usage_text": self.usage_var.get().strip(),
        }

    def get_region(self):
        """返回当前选中的地区名。"""
        return self.region_var.get()

    def set_users(self, users):
        """动态设置用户名单下拉选项，默认选第一项。"""
        self.user_combo["values"] = users
        if users:
            self.user_combo.current(0)

    def set_regions(self, regions):
        """动态更新地区下拉选项，优先选中默认地区。"""
        self.region_combo["values"] = regions
        if not regions:
            return
        # 当前已选有效则保留；否则优先默认地区，再退回第一项
        if self.region_var.get() in regions:
            return
        if self._default_region in regions:
            self.region_var.set(self._default_region)
        else:
            self.region_combo.current(0)