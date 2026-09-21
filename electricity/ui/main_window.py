"""主窗口：组装各面板，编排「计算」业务流程"""

import tkinter as tk
from tkinter import ttk, messagebox

from lib.calculator import Calculator
from lib.tariff_manager import TariffManager
from lib.history import HistoryManager
from ui.input_panel import InputPanel
from ui.result_panel import ResultPanel
from ui.record_table import RecordTable
from ui.more_panel import MorePanel


class MainWindow:
    """阶梯电价计算与查询系统主窗口。"""

    def __init__(self, root):
        self.root = root
        self.root.title("阶梯电价计算与查询系统")
        self.root.geometry("980x640")
        self.root.minsize(880, 560)

        # 业务对象
        self.tariff_manager = TariffManager()
        self.calculator = Calculator(self.tariff_manager)
        self.history = HistoryManager()

        self._build_ui()
        self._load_records()

    # ── 界面组装 ──
    def _build_ui(self):
        # 顶部输入区
        self.input_panel = InputPanel(
            self.root, self.tariff_manager.get_regions(), self.on_calculate,
            default_region="贵州",
        )
        self.input_panel.pack(fill="x", padx=12, pady=6)

        # 结果概览区
        self.result_panel = ResultPanel(self.root)
        self.result_panel.pack(fill="x", padx=12, pady=6)

        # 中部：左侧表格 + 右侧预留区
        mid = ttk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        self.record_table = RecordTable(mid)
        self.record_table.pack(side="left", fill="both", expand=True)

        self.more_panel = MorePanel(mid, width=260)
        self.more_panel.pack(side="right", fill="y", padx=(8, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=12, pady=(0, 6)
        )

    def _load_records(self):
        """启动时加载全部历史记录到表格。"""
        records = self.history.query(limit=500)
        self.record_table.load(records)

    # ── 业务编排 ──
    def on_calculate(self):
        """点击「计算」：校验 → 计算 → 显示 → 存库 → 刷表格。"""
        inputs = self.input_panel.get_inputs()
        errors = self._validate(inputs)
        if errors:
            messagebox.showwarning("提示", errors)
            return

        region = inputs["region"]
        usage = float(inputs["usage_text"])

        # 计算
        result = self.calculator.calculate(region, usage)

        # 显示结果
        self.result_panel.show_result(result)

        # 存库（用户名纯标签；月份可为空）
        username = inputs["username"] or None
        month = int(inputs["month"]) if inputs["month"] else None
        self.history.save(
            region, usage, result["total"], result["tiers"],
            result["current_tier"], username=username, month=month,
        )

        # 刷新表格（追加最新一条在顶部）
        latest = {
            "username": username or "",
            "month": month or "",
            "region": region,
            "usage": usage,
            "total": result["total"],
            "created_at": self._now_str(),
        }
        self.record_table.prepend(latest)

        # 状态更新
        dist = result["distance_to_next"]
        if dist["next_tier"] is not None:
            self.status_var.set(
                f"已保存：{username or '(匿名)'} 本月用电 {usage} 度，电费 "
                f"¥{result['total']:.2f} | 距第{dist['next_tier']}档还差 "
                f"{dist['remaining']:.1f} 度"
            )
        else:
            self.status_var.set(
                f"已保存：{username or '(匿名)'} 本月用电 {usage} 度，电费 "
                f"¥{result['total']:.2f}（最高档）"
            )

    @staticmethod
    def _validate(inputs):
        """输入校验，返回错误信息；无错返回空字符串。"""
        if not inputs["region"]:
            return "请选择地区"
        if not inputs["usage_text"]:
            return "请输入用电量"
        try:
            usage = float(inputs["usage_text"])
            if usage < 0:
                raise ValueError
        except ValueError:
            return "用电量必须是 ≥0 的有效数字"
        return ""

    @staticmethod
    def _now_str():
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")