"""主窗口：组装各面板，编排「计算」业务流程"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from lib.calculator import Calculator
from lib.tariff_manager import TariffManager
from lib.history import HistoryManager
from lib.user_manager import UserManager
from lib import exporter, importer, anomaly, validator
from lib.logger import get_logger
from ui.input_panel import InputPanel
from ui.result_panel import ResultPanel
from ui.record_table import RecordTable
from ui.more_panel import MorePanel

logger = get_logger()


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
        self.user_manager = UserManager()

        self._build_ui()
        self._load_records()

    # ── 界面组装 ──
    def _build_ui(self):
        # 顶部输入区
        self.input_panel = InputPanel(
            self.root, self.tariff_manager.get_regions(), self.on_calculate,
            default_region="贵州",
            users=self.user_manager.get_users(),
        )
        self.input_panel.pack(fill="x", padx=12, pady=6)

        # 结果概览区
        self.result_panel = ResultPanel(self.root)
        self.result_panel.pack(fill="x", padx=12, pady=6)

        # 中部：左侧(筛选+表格+异常) + 右侧预留区
        mid = ttk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)

        # 筛选栏
        self._build_filter_bar(left)

        self.record_table = RecordTable(left)
        self.record_table.pack(fill="both", expand=True)

        # 异常提示
        self.alert_var = tk.StringVar(value="")
        self.alert_label = ttk.Label(
            left, textvariable=self.alert_var, foreground="#b00000", anchor="w",
            wraplength=620, font=("", 9),
        )
        self.alert_label.pack(fill="x", pady=(4, 0))

        self.more_panel = MorePanel(
            mid, self.calculator,
            on_import_csv=self._on_import_csv,
            on_export=self._on_export,
            width=280,
        )
        self.more_panel.pack(side="right", fill="y", padx=(8, 0))
        self.more_panel.set_records(self._load_records_data())
        self.more_panel.set_region(self.input_panel.get_region())

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=12, pady=(0, 6)
        )

    def _build_filter_bar(self, parent):
        """构建筛选栏：按用户 / 月份筛选记录，含筛选与重置按钮。"""
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 4))

        ttk.Label(bar, text="筛选：").pack(side="left")
        ttk.Label(bar, text="用户").pack(side="left", padx=(4, 0))
        self.filter_user = ttk.Combobox(
            bar, state="readonly", width=8,
        )
        self.filter_user["values"] = self.user_manager.get_users()
        self.filter_user.pack(side="left", padx=4)
        ttk.Label(bar, text="月份").pack(side="left")
        self.filter_month = ttk.Combobox(
            bar, state="readonly", width=6,
            values=["全部"] + [str(m) for m in range(1, 13)],
        )
        self.filter_month.pack(side="left", padx=4)
        self.filter_month.current(0)

        ttk.Button(bar, text="筛选", command=self.apply_filter).pack(side="left", padx=6)
        ttk.Button(bar, text="重置", command=self.reset_filter).pack(side="left")

    def apply_filter(self):
        """按筛选条件加载记录，并重新检查异常。"""
        user = self.filter_user.get() or ""
        month = self.filter_month.get() or "全部"
        user_sel = user or None
        month_sel = None if month == "全部" else int(month)

        data = self._load_records_data(username=user_sel, month=month_sel)
        self.record_table.load(data)
        self.more_panel.set_records(data)
        self._update_alerts(data)
        self.status_var.set(f"筛选共 {len(data)} 条")

    def reset_filter(self):
        """重置筛选并显示全部记录。"""
        self.filter_user.set("")
        self.filter_month.current(0)
        self.apply_filter()

    def _load_records(self):
        """启动时加载全部历史记录到表格。"""
        self.record_table.load(self._load_records_data())
        self._update_alerts(self._load_records_data())

    def _load_records_data(self, username=None, month=None):
        """返回历史记录（支持按用户/月份筛选，代码表格和图表共用）。"""
        return self.history.query(username=username, month=month, limit=500)

    def _update_alerts(self, records):
        """对记录做异常检测并更新异常提示栏。"""
        from lib import anomaly
        alerts = anomaly.detect(records)
        if alerts:
            lines = "\n".join(f"⚠ {a['message']}" for a in alerts[:5])
            extra = f"（共 {len(alerts)} 条）" if len(alerts) > 5 else ""
            self.alert_var.set(f"异常提示：\n{lines}{extra}")
        else:
            self.alert_var.set("")

    # ── 业务编排 ──
    def on_calculate(self):
        """点击「计算」：校验 → 计算 → 显示 → 存库 → 刷表格。"""
        inputs = self.input_panel.get_inputs()

        # 统一校验（含用电量/月份/地区等边界），非法则提示并中止
        try:
            cleaned = validator.validate_record(
                inputs.get("username", ""),
                inputs.get("month", ""),
                inputs["region"],
                inputs["usage_text"],
            )
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
            return

        region = cleaned["region"]
        usage = cleaned["usage"]
        username = cleaned["username"]
        month = cleaned["month"]

        # 计算
        result = self.calculator.calculate(region, usage)
        logger.info("计算电费: 用户=%s 地区=%s 用电=%s度 电费=%.2f",
                    username or "(匿名)", region, usage, result["total"])

        # 显示结果
        self.result_panel.show_result(result)

        # 存库（用户名纯标签；月份可为空）
        self.history.save(
            region, usage, result["total"], result["tiers"],
            result["current_tier"], username=username or None, month=month,
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

        # 同步最新记录到图表区，并更新当前地区与异常提示
        self.more_panel.set_records(self._load_records_data())
        self.more_panel.set_region(region)
        self._update_alerts(self._load_records_data())

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

    # ── 导入/导出 ──
    def _on_import_csv(self):
        """选择 CSV 文件并批量导入用电记录，逐行计算电费后入库。"""
        path = filedialog.askopenfilename(
            title="选择要导入的 CSV 文件",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            records = importer.read_records(path, default_region=self.input_panel.get_region())
        except (OSError, ValueError) as exc:
            logger.error("CSV导入失败: %s", exc)
            messagebox.showerror("导入失败", str(exc))
            return

        ok_count = 0
        for rec in records:
            try:
                result = self.calculator.calculate(rec["region"], rec["usage"])
            except Exception as exc:  # 单行计算失败不中断整体
                self.status_var.set(f"导入：出行计算失败 {exc}")
                continue
            self.history.save(
                rec["region"], rec["usage"], result["total"], result["tiers"],
                result["current_tier"], username=rec["username"], month=rec["month"],
            )
            ok_count += 1

        msg = f"导入完成：成功 {ok_count} 条，跳过 {len(records) - ok_count} 条"
        logger.info("CSV导入: %s", msg)
        self.status_var.set(msg)
        self.more_panel.set_import_state(msg)
        self._refresh_after_change()
        messagebox.showinfo("导入完成", msg)

    def _on_export(self, fmt):
        """导出历史记录到 CSV 或 Excel。"""
        records = self._load_records_data()
        if not records:
            messagebox.showinfo("导出", "暂无记录可导出")
            return
        ext = ".csv" if fmt == "csv" else ".xlsx"
        path = filedialog.asksaveasfilename(
            title="导出记录",
            defaultextension=ext,
            filetypes=[(f"{fmt.upper()} 文件", f"*{ext}"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            count = exporter.export(records, path)
        except (ValueError, OSError, RuntimeError) as exc:
            logger.error("导出失败: %s", exc)
            messagebox.showerror("导出失败", str(exc))
            return
        logger.info("导出%d条记录 -> %s", count, path)
        self.status_var.set(f"已导出 {count} 条记录 -> {path}")

    def _refresh_after_change(self):
        """数据变更后刷新表格、图表、结果区。"""
        data = self._load_records_data()
        self.record_table.load(data)
        self.more_panel.set_records(data)
        self._update_alerts(data)

    @staticmethod
    def _now_str():
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")