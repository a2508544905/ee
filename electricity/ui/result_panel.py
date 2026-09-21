"""结果概览区：展示本次计算的总电费、当前档位、临界点"""

import tkinter as tk
from tkinter import ttk


class ResultPanel(ttk.LabelFrame):
    """一次计算结果的实时反馈区。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, text="计算结果", padding=12, **kwargs)

        # 三个核心指标卡片
        self.total_var = tk.StringVar(value="---")
        self.tier_var = tk.StringVar(value="---")
        self.dist_var = tk.StringVar(value="---")

        self._make_card(self, "总电费（元）", self.total_var, 0)
        self._make_card(self, "当前档位", self.tier_var, 1)
        self._make_card(self, "距下一档（度）", self.dist_var, 2)

    @staticmethod
    def _make_card(container, label, variable, col):
        """创建一个指标卡片。"""
        frame = ttk.Frame(container)
        frame.grid(row=0, column=col, padx=20, sticky="w")
        ttk.Label(frame, text=label, font=("微软雅黑", 9), foreground="#555555").pack(anchor="w")
        ttk.Label(frame, textvariable=variable, font=("微软雅黑", 18, "bold")).pack(anchor="w")

    def show_result(self, result):
        """填入一次计算结果。result 为 calculator.calculate() 的返回值。"""
        self.total_var.set(f"{result['total']:.2f}")
        self.tier_var.set(str(result["current_tier"]))

        dist = result["distance_to_next"]
        if dist["next_tier"] is not None:
            self.dist_var.set(f"{dist['remaining']:.1f}")
        else:
            self.dist_var.set("最高档")

    def reset(self):
        """清空显示。"""
        self.total_var.set("---")
        self.tier_var.set("---")
        self.dist_var.set("---")