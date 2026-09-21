"""程序入口 — 初始化档位配置、计算器、历史管理，启动主界面"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.tariff_manager import TariffManager
from lib.calculator import Calculator
from lib.history import HistoryManager
from lib.electricity import estimate_usage_by_budget


class ElectricityApp:
    """阶梯电价可视化计算与查询系统 — 主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title("阶梯电价可视化计算与查询系统")
        self.root.geometry("900x600")

        self.tariff_manager = TariffManager()
        self.calculator = Calculator(self.tariff_manager)
        self.history = HistoryManager()

        self._build_ui()

    def _build_ui(self):
        """构建界面布局。"""
        # ── 输入区 ──
        input_frame = ttk.LabelFrame(self.root, text="输入", padding=12)
        input_frame.pack(fill="x", padx=12, pady=6)

        ttk.Label(input_frame, text="地区：").grid(row=0, column=0, sticky="w")
        self.region_var = tk.StringVar()
        self.region_combo = ttk.Combobox(
            input_frame, textvariable=self.region_var, state="readonly", width=15
        )
        self.region_combo["values"] = self.tariff_manager.get_regions()
        if self.region_combo["values"]:
            self.region_combo.current(0)
        self.region_combo.grid(row=0, column=1, padx=8)

        ttk.Label(input_frame, text="用电量（度）：").grid(row=0, column=2, sticky="w")
        self.usage_entry = ttk.Entry(input_frame, width=15)
        self.usage_entry.grid(row=0, column=3, padx=8)

        ttk.Button(input_frame, text="计算", command=self.on_calculate).grid(row=0, column=4, padx=8)
        ttk.Button(input_frame, text="估算电量", command=self.on_estimate).grid(row=0, column=5, padx=8)

        # ── 结果区 ──
        result_frame = ttk.LabelFrame(self.root, text="计算结果", padding=12)
        result_frame.pack(fill="both", expand=True, padx=12, pady=6)

        columns = ("tier", "usage", "price", "amount")
        self.tree = ttk.Treeview(
            result_frame, columns=columns, show="headings", height=6
        )
        self.tree.heading("tier", text="档位")
        self.tree.heading("usage", text="用电量（度）")
        self.tree.heading("price", text="单价（元/度）")
        self.tree.heading("amount", text="金额（元）")
        self.tree.pack(fill="both", expand=True)

        # ── 状态区 ──
        self.status_var = tk.StringVar(value="请输入用电量后点击计算")
        ttk.Label(self.root, textvariable=self.status_var).pack(anchor="w", padx=12, pady=4)

    def on_calculate(self):
        """计算电费。"""
        region = self.region_var.get()
        usage_text = self.usage_entry.get().strip()

        if not region:
            messagebox.showwarning("提示", "请选择地区")
            return
        if not usage_text:
            messagebox.showwarning("提示", "请输入用电量")
            return

        try:
            usage = float(usage_text)
            if usage < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "用电量必须是有效数字")
            return

        result = self.calculator.calculate(region, usage)

        # 更新表格
        self.tree.delete(*self.tree.get_children())
        for t in result["tiers"]:
            self.tree.insert("", "end", values=(t["tier"], t["usage"], t["price"], t["amount"]))
        self.tree.insert("", "end", values=("合计", usage, "-", result["total"]))

        # 临界点提示
        dist = result["distance_to_next"]
        if dist["next_tier"] is not None:
            self.status_var.set(
                f"当前第{result['current_tier']}档 | "
                f"距第{dist['next_tier']}档还差 {dist['remaining']:.1f} 度 | "
                f"超出后每度多 {dist['price_diff']:.2f} 元"
            )
        else:
            self.status_var.set(f"当前第{result['current_tier']}档（最高档）| 总电费 ¥{result['total']:.2f}")

        # 保存历史
        self.history.save(region, usage, result["total"], result["tiers"], result["current_tier"])


    def on_estimate(self):
        """根据预算反推可使用电量。"""
        region = self.region_var.get()
        budget_text = self.usage_entry.get().strip()

        if not region:
            messagebox.showwarning("提示", "请选择地区")
            return
        if not budget_text:
            messagebox.showwarning("提示", "请在用电量输入框中输入预算金额")
            return

        try:
            budget = float(budget_text)
            if budget <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "预算必须是正数")
            return

        tiers = self.tariff_manager.get_tiers(region)
        usage = estimate_usage_by_budget(budget, tiers)
        self.status_var.set(f"预算 ¥{budget:.2f} 可用电量约 {usage:.1f} 度")


def main():
    root = tk.Tk()
    app = ElectricityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
