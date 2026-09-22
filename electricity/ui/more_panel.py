"""右侧功能区：CSV导入 / 导出 / 统计图表"""

import csv
import tkinter as tk
from tkinter import ttk

from ui.chart_view import ChartWindow


class MorePanel(ttk.LabelFrame):
    """右侧功能区，用选项卡承载功能。

    - CSV 导入 / 导出：批量处理用电记录
    - 统计图表：点击按钮弹出独立 ChartWindow，三类图在大版面绘制
    """

    def __init__(self, master, calculator, on_import_csv=None, on_export=None, **kwargs):
        super().__init__(master, text="更多功能", padding=8, **kwargs)

        self.calculator = calculator
        self._on_import_csv = on_import_csv   # 回调：发起 CSV 导入
        self._on_export = on_export           # 回调：发起记录导出(fmt)
        self._records = []          # 由外部注入的历史记录
        self._current_region = "贵州"

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self._build_chart_tab()
        self._build_import_tab()
        self._build_export_tab()

    # ── 导入 tab ──
    def _build_import_tab(self):
        """CSV 批量导入：选择文件并导入。"""
        page = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(page, text="CSV导入")

        ttk.Label(
            page, text="从 CSV 批量导入用电记录",
            anchor="w", wraplength=200,
        ).pack(anchor="w", pady=(0, 4))
        ttk.Label(
            page, text="支持表头：用户名/月份/地区/用电量\n"
                       "或不带表头（按：用户,月份,地区,用电量）",
            foreground="#888888", font=("", 9), anchor="w", wraplength=200,
        ).pack(anchor="w", pady=(0, 8))

        self.import_btn = ttk.Button(page, text="选择 CSV 文件并导入", command=self._on_import_csv)
        self.import_btn.pack(anchor="w")
        ttk.Button(page, text="下载导入模板", command=self._download_template).pack(
            anchor="w", pady=(6, 0))

        self.import_state = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.import_state, foreground="#666666", font=("", 9),
                  anchor="w").pack(fill="x", padx=12, pady=(0, 4))

    # ── 导出 tab ──
    def _download_template(self):
        """生成并下载 CSV 导入模板（表头 + 示例行）。"""
        from tkinter import filedialog, messagebox
        path = filedialog.asksaveasfilename(
            parent=self.master, defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile="导入模板.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["用户名", "月份", "地区", "用电量"])
                w.writerow(["A", "1", "贵州", "300"])
                w.writerow(["B", "2", "贵州", "1500"])
            messagebox.showinfo("已下载", f"导入模板已保存到：\n{path}")
        except Exception as exc:
            messagebox.showerror("下载失败", str(exc))

    def _build_export_tab(self):
        """导出历史记录为 CSV 或 Excel。"""
        page = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(page, text="导出")

        ttk.Label(
            page, text="将云端历史记录导出",
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        ttk.Button(page, text="导出为 CSV", compound="center",
                   command=lambda: self._on_export("csv")).pack(anchor="w", fill="x", pady=3)
        ttk.Button(page, text="导出为 Excel(.xlsx)",
                   command=lambda: self._on_export("xlsx")).pack(anchor="w", fill="x", pady=3)

    def set_import_state(self, text):
        """设置导入结果提示。"""
        self.import_state.set(text)

    # ── 图表 tab ──
    def _build_chart_tab(self):
        """构建统计图表 tab：类型选择 + 打开独立窗口按钮。"""
        page = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(page, text="统计图表")

        ttk.Label(page, text="图表类型：").pack(anchor="w", pady=(0, 4))
        self._chart_kind = ttk.Combobox(
            page, state="readonly", width=16,
            values=["用电趋势图", "阶梯费用图", "用户对比图",
                    "档位分布图", "电费构成图"],
        )
        self._chart_kind.current(0)
        self._chart_kind.pack(anchor="w", fill="x")

        # 阶梯费用图需要输入用电量
        self._usage_row = ttk.Frame(page)
        ttk.Label(self._usage_row, text="用电量(度)：").pack(side="left")
        self._usage_entry = ttk.Entry(self._usage_row, width=12)
        self._usage_entry.pack(side="left")

        ttk.Button(page, text="打开图表窗口", command=self._open_chart).pack(anchor="w", pady=(12, 4))
        ttk.Label(
            page, text="图表将在独立窗口完整展示",
            foreground="#888888", font=("", 9),
        ).pack(anchor="w")

        self._chart_kind.bind("<<ComboboxSelected>>", self._on_kind_changed)

    def set_records(self, records):
        """供外部注入最新历史记录。"""
        self._records = records

    def set_region(self, region):
        """供外部同步当前选中的地区。"""
        self._current_region = region

    def _on_kind_changed(self, _event=None):
        """切换图表类型时，控制用电量输入行的显隐。"""
        if self._chart_kind.get() in ("阶梯费用图", "电费构成图"):
            self._usage_row.pack(anchor="w", pady=(8, 0))
        else:
            self._usage_row.pack_forget()

    def _open_chart(self):
        """根据选中的类型弹出独立图表窗口。"""
        kind = self._chart_kind.get()
        win = ChartWindow(self.master, title=f"统计图表 - {kind}")

        if kind == "用电趋势图":
            win.show_trend(self._records)
        elif kind == "用户对比图":
            win.show_user_compare(self._records)
        elif kind == "档位分布图":
            win.show_tier_distribution(self._records)
        elif kind in ("阶梯费用图", "电费构成图"):
            usage_text = self._usage_entry.get().strip()
            try:
                usage = float(usage_text)
            except ValueError:
                win._empty("请输入有效用电量后再绘制")
                return
            result = self.calculator.calculate(self._current_region, usage)
            if kind == "阶梯费用图":
                win.show_tier(result)
            else:
                win.show_fee_composition(result)
        else:
            win.destroy()