"""主窗口：组装各面板，编排「计算」业务流程"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from lib.calculator import Calculator
from lib.tariff_manager import TariffManager
from lib.history import HistoryManager
from lib.user_manager import UserManager
from lib.data_loader import DataLoader
from lib import exporter, anomaly, report_exporter, summary
from lib.logger import get_logger
from ui import theme
from ui.tariff_panel import open_tariff_window
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
        self.root.geometry("1020x660")
        self.root.minsize(880, 560)

        # 应用暗色霓虹科技主题
        self.style = theme.apply_theme()
        self.root.configure(background=theme.BG_DEEP)

        # 业务对象
        self.tariff_manager = TariffManager()
        self.calculator = Calculator(self.tariff_manager)
        self.history = HistoryManager()
        self.user_manager = UserManager()
        self.data_loader = DataLoader(self.calculator)  # CSV导入 + JSON持久化
        self._persist_to_json()  # 启动时把 SQLite 记录同步写入 records.json

        self._build_ui()
        self._build_menu()
        self._load_records()

    def _build_menu(self):
        """构建顶部菜单栏：设置 → 档位规则管理。"""
        menubar = tk.Menu(self.root, bg=theme.BG_ELEV, fg=theme.TEXT_MAIN,
                          activebackground=theme.BG_PANEL, activeforeground=theme.NEON_CYAN)
        settings = tk.Menu(menubar, tearoff=0, bg=theme.BG_ELEV, fg=theme.TEXT_MAIN,
                           activebackground=theme.BG_PANEL, activeforeground=theme.NEON_CYAN)
        settings.add_command(label="档位规则管理", command=self.open_tariff_manager)
        settings.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="设置", menu=settings)
        self.root.config(menu=menubar)

    def open_tariff_manager(self):
        """打开档位规则管理窗口，修改后刷新地区下拉。"""
        open_tariff_window(self.root, self.tariff_manager, on_changed=self._on_tariff_changed)

    def _on_tariff_changed(self, region):
        """档位配置变更后：刷新地区下拉与计算器，并重新计算默认值。"""
        regions = self.tariff_manager.get_regions()
        self.input_panel.set_regions(regions)
        # 新变更地区作为默认选中，便于立即验证
        if region in regions:
            self.input_panel.set_region_by_name(region)

    # ── 界面组装 ──
    def _build_ui(self):
        outer = ttk.Frame(self.root, style="Root.TFrame")
        outer.pack(fill="both", expand=True, padx=8, pady=8)

        # 顶部科技标题条
        self._build_header(outer)

        # 顶部输入区
        self.input_panel = InputPanel(
            outer, self.tariff_manager.get_regions(), self.on_calculate,
            default_region="贵州",
            users=self.user_manager.get_users(),
        )
        self.input_panel.pack(fill="x", padx=12, pady=6)

        # 结果概览区
        self.result_panel = ResultPanel(outer)
        self.result_panel.pack(fill="x", padx=12, pady=6)

        # 中部：左侧(筛选+表格+异常) + 右侧预留区
        mid = ttk.Frame(outer)
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)

        # 筛选栏
        self._build_filter_bar(left)

        # 汇总统计条（当前记录集合的聚合指标）
        self.summary_var = tk.StringVar(value="")
        ttk.Label(
            left, textvariable=self.summary_var, style="Dim.TLabel",
            font=("Consolas", 9), anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.record_table = RecordTable(left)
        self.record_table.pack(fill="both", expand=True)

        # 异常提示
        self.alert_var = tk.StringVar(value="")
        alert_row = ttk.Frame(left)
        alert_row.pack(fill="x", pady=(4, 0))
        self.alert_label = ttk.Label(
            alert_row, textvariable=self.alert_var, foreground=theme.DANGER,
            anchor="w", wraplength=560, font=("", 9),
        )
        self.alert_label.pack(side="left", fill="x", expand=True)
        self.export_alert_btn = ttk.Button(
            alert_row, text="导出异常报告", command=self._export_alert_report)
        self.export_alert_btn.pack(side="right", padx=(6, 0))
        self._alerts = []

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
        ttk.Label(outer, textvariable=self.status_var, style="Dim.TLabel",
                  font=("Consolas", 9), anchor="w").pack(
            fill="x", padx=12, pady=(0, 6)
        )

    def _build_header(self, parent):
        """构建顶部科技感标题条：系统名 + 霓虹分隔线。"""
        header = ttk.Frame(parent, style="Root.TFrame")
        header.pack(fill="x", padx=4, pady=(0, 8))

        ttk.Label(
            header, text="⚡ 阶梯电价可视化计算与查询系统",
            style="Root.TLabel", font=("Microsoft YaHei", 15, "bold"),
            foreground=theme.NEON_CYAN,
        ).pack(side="left")

        ttk.Label(
            header, text=" SMART TARIFF ANALYZER ",
            style="Root.TLabel", font=("Consolas", 9), foreground=theme.TEXT_DIM,
        ).pack(side="right")

        # 霓虹分隔线
        sep = ttk.Separator(parent, orient="horizontal")
        sep.pack(fill="x", pady=(0, 6))

    def _build_filter_bar(self, parent):
        """构建筛选栏：按用户 / 月份筛选记录，含筛选与重置按钮。"""
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 4))

        ttk.Label(bar, text="筛选：", style="Dim.TLabel").pack(side="left")
        ttk.Label(bar, text="用户", style="Dim.TLabel").pack(side="left", padx=(4, 0))
        self.filter_user = ttk.Combobox(
            bar, state="normal", width=10,
        )
        self.filter_user["values"] = self.user_manager.get_users()
        self.filter_user.pack(side="left", padx=4)
        ttk.Label(bar, text="月份", style="Dim.TLabel").pack(side="left")
        self.filter_month = ttk.Combobox(
            bar, state="readonly", width=6,
            values=["全部"] + [str(m) for m in range(1, 13)],
        )
        self.filter_month.pack(side="left", padx=4)
        self.filter_month.current(0)

        ttk.Label(bar, text="用电量(度)", style="Dim.TLabel").pack(side="left", padx=(8, 0))
        self.filter_usage_min = ttk.Entry(bar, width=7)
        self.filter_usage_min.pack(side="left", padx=2)
        ttk.Label(bar, text="~", style="Dim.TLabel").pack(side="left")
        self.filter_usage_max = ttk.Entry(bar, width=7)
        self.filter_usage_max.pack(side="left", padx=2)

        ttk.Button(bar, text="筛选", command=self.apply_filter).pack(side="left", padx=6)
        ttk.Button(bar, text="重置", command=self.reset_filter).pack(side="left")

    def _parse_usage_range(self):
        """解析用电量区间输入；非法传回(None, None, 错误信息)。"""
        min_s = self.filter_usage_min.get().strip()
        max_s = self.filter_usage_max.get().strip()
        if not min_s and not max_s:
            return None, None, None
        try:
            lo = float(min_s) if min_s else None
            hi = float(max_s) if max_s else None
        except ValueError:
            return None, None, "用电量区间必须是数字"
        if lo is not None and lo < 0:
            return None, None, "用电量下限不能为负数"
        if hi is not None and hi < 0:
            return None, None, "用电量上限不能为负数"
        if lo is not None and hi is not None and lo > hi:
            return None, None, "用电量下限不能大于上限"
        return lo, hi, None

    def apply_filter(self):
        """按筛选条件加载记录，并重新检查异常。"""
        user = self.filter_user.get() or ""
        month = self.filter_month.get() or "全部"
        user_sel = user or None
        month_sel = None if month == "全部" else int(month)

        lo, hi, err = self._parse_usage_range()
        if err:
            messagebox.showwarning("提示", err)
            return

        data = self._load_records_data(
            username=user_sel, month=month_sel, min_usage=lo, max_usage=hi)
        self.record_table.load(data)
        self.more_panel.set_records(data)
        self._update_summary(data)
        self._update_alerts(data)
        self.status_var.set(f"筛选共 {len(data)} 条")

    def reset_filter(self):
        """重置筛选并显示全部记录。"""
        self.filter_user.set("")
        self.filter_month.current(0)
        self.filter_usage_min.delete(0, tk.END)
        self.filter_usage_max.delete(0, tk.END)
        self.apply_filter()

    def _load_records(self):
        """启动时加载全部历史记录到表格。"""
        data = self._load_records_data()
        self.record_table.load(data)
        self._update_summary(data)
        self._update_alerts(data)

    def _update_summary(self, records):
        """用当前记录集合刷新汇总统计条。"""
        self.summary_var.set(summary.format_summary_text(summary.summarize(records)))

    def _load_records_data(self, username=None, month=None, min_usage=None, max_usage=None):
        """返回历史记录（可按用户/月份/用电量区间筛选）。"""
        return self.history.query(username=username, month=month,
                                  min_usage=min_usage, max_usage=max_usage, limit=500)

    def _persist_to_json(self):
        """把当前全部 SQLite 记录同步写入 data/records.json（JSON 持久化）。"""
        try:
            records = self.history.query(limit=5000)
            json_records = [
                {"username": r.get("username") or "", "month": r.get("month"),
                 "region": r.get("region") or "", "usage": r.get("usage") or 0,
                 "total": r.get("total") or 0}
                for r in records
            ]
            self.data_loader.save_records(json_records)
        except Exception as exc:
            logger.warning("JSON持久化失败: %s", exc)

    def _update_alerts(self, records):
        """对记录做异常检测并更新异常提示栏。"""
        from lib import anomaly
        alerts = anomaly.detect(records)
        self._alerts = alerts
        if alerts:
            lines = "\n".join(f"⚠ {a['message']}" for a in alerts[:5])
            extra = f"（共 {len(alerts)} 条）" if len(alerts) > 5 else ""
            self.alert_var.set(f"异常提示：\n{lines}{extra}")
        else:
            self.alert_var.set("")

    def _export_alert_report(self):
        """把当前异常检测结果导出为 CSV 报告。"""
        if not self._alerts:
            messagebox.showinfo("提示", "当前没有异常记录可导出")
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile="异常报告.csv")
        if not path:
            return
        from lib import exporter
        n = exporter.export_alerts(self._alerts, path)
        messagebox.showinfo("已导出", f"已导出 {n} 条异常到：\n{path}")

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
        self._persist_to_json()  # 录入后同步到 JSON 持久化

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

        # 同步最新记录到图表区，并更新当前地区、汇总与异常提示
        data = self._load_records_data()
        self.more_panel.set_records(data)
        self.more_panel.set_region(region)
        self._update_summary(data)
        self._update_alerts(data)

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
            csv_records = self.data_loader.load_csv(
                path, default_region=self.input_panel.get_region())
        except (OSError, ValueError) as exc:
            logger.error("CSV导入失败: %s", exc)
            messagebox.showerror("导入失败", str(exc))
            return

        ok_count = 0
        for rec in csv_records:
            try:
                self.history.save(
                    rec["region"], rec["usage"], rec["total"], rec["tiers"],
                    rec["current_tier"], username=rec["username"], month=rec["month"],
                )
            except Exception as exc:  # 单行入库失败不中断整体
                self.status_var.set(f"导入：单行入库失败 {exc}")
                continue
            ok_count += 1

        self._persist_to_json()  # 导入后同步到 JSON 持久化

        msg = f"导入完成：成功 {ok_count} 条，跳过 {len(csv_records) - ok_count} 条"
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
            count = report_exporter.export(records, path)
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
        self._update_summary(data)
        self._update_alerts(data)

    @staticmethod
    def _now_str():
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")