"""图表窗口 — 用 matplotlib 生成可视化统计图，独立弹窗展示

提供三类图，均以独立 Toplevel 窗口承载，获得充足版面：
  - trend_chart   用电趋势图（双轴：用电量 / 电费，随时间变化）
  - tier_chart    阶梯费用图（累计电费随用电量增长的阶梯曲线，呼应“阶梯”主题）
  - user_chart    用户对比图（按用户聚合用电量对比）
"""

from datetime import datetime
from tkinter import Toplevel, ttk

import matplotlib
matplotlib.use("TkAgg")  # 明确使用 Tk 后端，保证能嵌入 tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


_FONT_CONFIGURED = False


def _setup_chinese_font():
    """配置 matplotlib 使用中文字体，否则中文标题/标签会显示成方块。

    优先用系统常见中文字体（黑体/微软雅黑），并允许外部显式指定。
    """
    global _FONT_CONFIGURED
    if _FONT_CONFIGURED:
        return  # 只配置一次，避免重复设置

    candidates = []
    env = __import__("os").environ.get("CHART_FONT")
    if env:
        candidates.append(env)
    candidates += ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]

    try:
        from matplotlib import rcParams
        rcParams["font.sans-serif"] = candidates
        rcParams["axes.unicode_minus"] = False  # 让负号正常显示（不用unicode减号）
        _FONT_CONFIGURED = True
    except Exception:
        pass  # 字体配置失败不阻断绘图，最多中文变方块


_setup_chinese_font()


class ChartWindow(Toplevel):
    """独立的图表窗口。创建即显示，关闭即销毁。"""

    def __init__(self, master, title="统计图表"):
        super().__init__(master)
        self.title(title)
        self.geometry("760x520")
        self.minsize(560, 400)

        self.figure = Figure(figsize=(7.5, 4.8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 底部工具条：保存图片
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="💾 保存为图片(PNG)", command=self.save_png).pack(side="right")

        self._screen_record = None  # 供阶梯图复用当前计算结果

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

    @staticmethod
    def _short_time(created_at):
        """把 'YYYY-MM-DD HH:MM:SS' 压缩成 'MM-DD'，用于横轴标签。"""
        try:
            return datetime.strptime(created_at[:16], "%Y-%m-%d %H:%M").strftime("%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(created_at)

    def _empty(self, text):
        """无数据时显示居中提示。"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, text, ha="center", va="center",
                transform=ax.transAxes, color="#888888", fontsize=12)
        ax.axis("off")
        self.canvas.draw()

    # ── 1. 用电趋势图（双轴）──
    def show_trend(self, records):
        """横轴为记录时间，左轴用电量、右轴电费，双轴避免数值量级互相压扁。"""
        self.figure.clear()
        records = sorted(records, key=lambda r: r["created_at"])
        if not records:
            self._empty("暂无历史数据")
            return
        labels = [self._short_time(r["created_at"]) for r in records]
        usages = [r["usage"] for r in records]
        totals = [r["total"] for r in records]

        ax1 = self.figure.add_subplot(111)
        ax1.plot(labels, usages, marker="o", color="#2f80ed", label="用电量(度)")
        ax1.set_xlabel("记录时间")
        ax1.set_ylabel("用电量(度)", color="#2f80ed")
        ax1.tick_params(axis="y", labelcolor="#2f80ed")
        ax1.grid(True, linestyle="--", alpha=0.4)

        ax2 = ax1.twinx()
        ax2.plot(labels, totals, marker="s", color="#eb5757", label="电费(元)")
        ax2.set_ylabel("电费(元)", color="#eb5757")
        ax2.tick_params(axis="y", labelcolor="#eb5757")

        # 合并两条曲线的图例
        lines = ax1.get_lines() + ax2.get_lines()
        self.figure.legend(lines, [l.get_label() for l in lines], loc="upper left")

        if len(labels) > 6:
            ax1.tick_params(axis="x", rotation=30, labelsize=8)
        self.figure.tight_layout()
        self.canvas.draw()

    # ── 2. 阶梯费用图（核心：阶梯曲线）──
    def show_tier(self, result):
        """画出「累计电费 vs 用电量」的阶梯折线，直观展示跳档。

        Uses:
            result: calculator.calculate() 的返回，含 usage / tiers / total。
        """
        self.figure.clear()
        usage = result["usage"]
        tiers = result["tiers"]  # [{tier,min,max,price,usage,amount}, ...]
        colors = ["#2f80ed", "#f2994a", "#eb5757"]

        # 累计费用随用量：每档内部斜率=单价，档位边界处产生折点
        xs = []
        ys = []
        cum_fee = 0.0
        x = 0.0
        for t in tiers:
            if t["usage"] <= 0:
                continue
            x_end = x + t["usage"]
            fee_end = cum_fee + t["usage"] * t["price"]
            # 档内从 (x, cum_fee) 到 (x_end, fee_end) 的一段
            xs.extend([x, x_end])
            ys.extend([cum_fee, fee_end])
            x = x_end
            cum_fee = fee_end

        ax = self.figure.add_subplot(111)

        # 各档位区间用半透明色带标注（第一/二/三档）
        prev = 0.0
        for idx, t in enumerate(tiers):
            if t["usage"] <= 0:
                continue
            ax.axvspan(prev, prev + t["usage"],
                       color=colors[idx % len(colors)], alpha=0.10)
            prev += t["usage"]

        # 阶梯折线（steps-post 让折点在档位边界处）
        ax.plot(xs, ys, drawstyle="steps-post", marker="o",
                color="#2f80ed", linewidth=2.2, label="累计电费")

        # 档位边界竖虚线 + 单价标注
        cx = 0.0
        cy = 0.0
        for idx, t in enumerate(tiers):
            if t["usage"] <= 0:
                continue
            cx += t["usage"]
            cy += t["usage"] * t["price"]
            ax.axvline(cx, color="#bbbbbb", linestyle="--", linewidth=1)
            ax.text(cx, cy, f" {t['price']}元/度", fontsize=9,
                    color=colors[idx % len(colors)], verticalalignment="bottom")

        # 当前用电量位置标注
        ax.axvline(usage, color="#333333", linestyle="-", linewidth=1.4)
        ax.annotate(
            f"总电费 ¥{result['total']:.2f}\n({usage:.0f}度)",
            xy=(usage, result["total"]),
            xytext=(usage * 0.45, result["total"] * 0.8),
            arrowprops=dict(arrowstyle="->", color="#333333"),
            fontsize=10,
        )

        ax.set_title(f"{result['region']} · 用电 {usage:.0f} 度 · 总电费 ¥{result['total']:.2f}")
        ax.set_xlabel("累计用电量(度)")
        ax.set_ylabel("累计电费(元)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_xlim(0, usage * 1.15)
        self.figure.tight_layout()
        self.canvas.draw()

    # ── 4. 档位分布图（用电量在各档位区间分布）──
    def show_tier_distribution(self, records):
        """按档案用电量所在档位分组，柱状图展示各档记录数与用电总量。"""
        self.figure.clear()
        if not records:
            self._empty("暂无历史数据")
            return
        # 直接用记录里的 current_tier 字段聚合
        agg = {}
        labels = []
        for r in records:
            tier = r.get("current_tier") or 0
            tier = int(tier)
            a = agg.setdefault(tier, [0, 0.0])  # [记录数, 用电量]
            a[0] += 1
            a[1] += r.get("usage") or 0
        if not agg:
            self._empty("暂无档位数据")
            return
        items = sorted(agg.items())
        labels = [f"第{t}档" for t, _ in items]
        counts = [v[0] for _, v in items]
        usages = [v[1] for _, v in items]

        ax = self.figure.add_subplot(111)
        x = list(range(len(labels)))
        bars = ax.bar(x, usages, color="#9d7bff", alpha=0.85)
        for xi, (u, c) in enumerate(zip(usages, counts)):
            ax.text(xi, u, f"{u:.0f}度\n{c}条", ha="center", va="bottom", fontsize=9,
                    color="#9d7bff")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title("用电量档位分布")
        ax.set_xlabel("档位")
        ax.set_ylabel("总用电量(度)")
        ax.grid(True, linestyle="--", alpha=0.4, axis="y")
        self.figure.tight_layout()
        self.canvas.draw()

    # ── 5. 电费构成饼图（各档电费贡献占比）──
    def show_fee_composition(self, result):
        """按当前计算结果的各档费用绘制饼图，展示每档对总电费的贡献。"""
        self.figure.clear()
        usage = result["usage"]
        tiers = result.get("tiers") or []
        # 只统计实际用到的档（用量>0）
        used = [t for t in tiers if t.get("usage", 0) > 0]
        if not used or result.get("total", 0) <= 0:
            self._empty("当前用电量未产生电费，无法构成饼图")
            return

        labels = [f"第{t['tier']}档\n{t['amount']:.2f}元" for t in used]
        values = [t["amount"] for t in used]
        colors = ["#2f80ed", "#f2994a", "#eb5757", "#9b51e0", "#27ae60"]

        ax = self.figure.add_subplot(111)
        wedges, _ = ax.pie(
            values, labels=labels, colors=colors[:len(used)],
            autopct="%1.1f%%", startangle=90,
            textprops={'fontsize': 10},
        )
        ax.axis("equal")
        ax.set_title(
            f"{result['region']} · 用电 {usage:.0f} 度 · 电费构成 (¥{result['total']:.2f})")
        self.figure.tight_layout()
        self.canvas.draw()

    # ── 3. 用户对比图（按用户聚合）──
    def show_user_compare(self, records):
        """按用户名聚合总用电量/总电费，柱状图对比。"""
        self.figure.clear()
        if not records:
            self._empty("暂无历史数据")
            return
        # 聚合：name -> (总用电量, 总电费)
        agg = {}
        for r in records:
            name = r["username"] or "匿名"
            a = agg.setdefault(name, [0.0, 0.0])
            a[0] += r["usage"]
            a[1] += r["total"]
        names = list(agg)
        usages = [agg[n][0] for n in names]
        totals = [agg[n][1] for n in names]

        ax = self.figure.add_subplot(111)
        ax.bar(names, usages, color="#2f80ed", alpha=0.85, label="总用电量(度)")
        for x, u in enumerate(usages):
            ax.text(x, u, f"{u:.0f}", ha="center", va="bottom", fontsize=9, color="#2f80ed")
        ax.set_title("各用户用电量对比")
        ax.set_xlabel("用户")
        ax.set_ylabel("总用电量(度)")
        ax.grid(True, linestyle="--", alpha=0.4, axis="y")
        if len(names) > 6:
            ax.tick_params(axis="x", rotation=30, labelsize=8)
        self.figure.tight_layout()
        self.canvas.draw()