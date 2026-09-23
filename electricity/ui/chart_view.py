"""图表窗口 — 将 lib/chart_generator 生成的图表嵌入 tkinter 弹窗展示

职责：
  - 创建独立的图表窗口（Toplevel），承载 matplotlib Figure
  - 绘图通过 lib/chart_generator 完成（返回 Figure），本层只负责嵌入与保存
"""

from tkinter import Toplevel, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from lib import chart_generator


class ChartWindow(Toplevel):
    """独立的图表窗口。创建即显示，关闭即销毁。"""

    def __init__(self, master, title="统计图表"):
        super().__init__(master)
        self.title(title)
        self.geometry("760x520")
        self.minsize(560, 400)

        self.figure = chart_generator._new_figure()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 底部工具条：保存图片
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="保存为图片(PNG)", command=self.save_png).pack(side="right")

    def save_png(self):
        """把当前图表另存为 PNG 图片文件。"""
        from tkinter import filedialog
        from tkinter import messagebox
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".png",
            filetypes=[("PNG 图片", "*.png")],
            initialfile=self.title().replace(" ", "_") + ".png")
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=150, bbox_inches="tight")
            messagebox.showinfo("已保存", f"图片已保存到：\n{path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _show(self, fig):
        """把指定 Figure 渲染到画布上。"""
        self.figure = fig
        self.canvas.figure = fig
        self.canvas.draw()

    # ── 1. 用电趋势图 ──
    def show_trend(self, records):
        """显示用电趋势图（双轴）。"""
        self._show(chart_generator.generate_trend_chart(records))

    # ── 2. 阶梯费用图 ──
    def show_tier(self, result):
        """显示阶梯费用图。"""
        self._show(chart_generator.generate_tier_chart(result))

    # ── 3. 用户对比图 ──
    def show_user_compare(self, records):
        """显示用户对比图。"""
        self._show(chart_generator.generate_user_chart(records))

    # ── 4. 档位分布图 ──
    def show_tier_distribution(self, records):
        """显示档位分布图。"""
        self._show(chart_generator.generate_tier_distribution_chart(records))

    # ── 5. 电费构成饼图 ──
    def show_fee_composition(self, result):
        """显示电费构成饼图。"""
        self._show(chart_generator.generate_fee_composition_chart(result))