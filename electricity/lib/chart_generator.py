"""图表生成 — 用 matplotlib 生成统计图表（纯业务层，不依赖 tkinter）

职责：
  - 根据记录数据生成各类图表对应的 Figure 对象
  - 只负责绘图与返回 Figure，不负责界面展示（展示交给 ui/ 层）

约定：
  - 每个函数返回 matplotlib.figure.Figure
  - 独立函数、以动词开头、中文注释
"""

from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # 无界面后端，只生成 Figure，由 UI 层嵌入
from matplotlib.figure import Figure

# 图表面板尺寸与像素密度
_FIG_SIZE = (7.5, 4.8)
_DPI = 100

# 各图配色（与暗色科技主题协调）
_COLORS = ["#2f80ed", "#f2994a", "#eb5757", "#9b51e0", "#27ae60"]
_COLOR_MAIN = "#2f80ed"
_COLOR_ACCENT = "#eb5757"

_FONT_CONFIGURED = False


def _setup_chinese_font():
    """配置 matplotlib 中文字体，避免中文标题/标签显示为方块（只配置一次）。"""
    global _FONT_CONFIGURED
    if _FONT_CONFIGURED:
        return
    try:
        from matplotlib import rcParams
        rcParams["font.sans-serif"] = [
            "Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS",
        ]
        rcParams["axes.unicode_minus"] = False  # 负号正常显示
        _FONT_CONFIGURED = True
    except Exception:
        pass  # 字体配置失败不阻断绘图


_setup_chinese_font()


def _new_figure():
    """创建并返回一个空白 Figure 对象。"""
    return Figure(figsize=_FIG_SIZE, dpi=_DPI)


def _empty_figure(text):
    """在空白 Figure 上写居中的提示文字（无数据时使用）。"""
    fig = _new_figure()
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, text, ha="center", va="center",
            transform=ax.transAxes, color="#888888", fontsize=12)
    ax.axis("off")
    return fig


def _daily_key(created_at):
    """把 'YYYY-MM-DD HH:MM:SS' 压缩成日期 'MM-DD'，用于按天汇总横轴。"""
    try:
        return datetime.strptime(str(created_at)[:10], "%Y-%m-%d").strftime("%m-%d")
    except (ValueError, TypeError):
        return str(created_at)[:10]


def generate_trend_chart(records):
    """生成用电趋势图：按天汇总，横轴日期，左轴用电量、右轴电费（双轴）。

    说明：为了清晰展示，横坐标改为「天」粒度（每天汇总电量与电费），
    避免小时级时间戳过多导致标签重叠；所有原始数据点保留，不做异常剔除。

    Args:
        records: 历史记录列表，按 created_at 升序、按天聚合绘制。

    Returns:
        Figure: 双轴柱线组合图（电量柱 + 电费线）。
    """
    records = [r for r in (records or [])]
    if not records:
        return _empty_figure("暂无历史数据")

    # 按天聚合：累计每日电量与电费
    agg = {}
    for r in records:
        day = _daily_key(r.get("created_at"))
        d = agg.setdefault(day, [0.0, 0.0])
        d[0] += r.get("usage") or 0
        d[1] += r.get("total") or 0
    days = sorted(agg)                      # 横轴日期（"MM-DD"）
    usages = [agg[d][0] for d in days]
    totals = [agg[d][1] for d in days]

    fig = _new_figure()
    ax1 = fig.add_subplot(111)
    xpos = list(range(len(days)))
    # 左轴：每日用电量柱状图
    ax1.bar(xpos, usages, color=_COLOR_MAIN, alpha=0.8, label="用电量(度)")
    ax1.set_xlabel("记录日期")
    ax1.set_ylabel("用电量(度)", color=_COLOR_MAIN)
    ax1.tick_params(axis="y", labelcolor=_COLOR_MAIN)
    ax1.set_xticks(xpos)
    ax1.set_xticklabels(days, rotation=30, ha="right", fontsize=8)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="y")

    # 右轴：每日电费折线
    ax2 = ax1.twinx()
    ax2.plot(xpos, totals, color=_COLOR_ACCENT, marker="o",
             markersize=4, linewidth=1.8, label="电费(元)")
    ax2.set_ylabel("电费(元)", color=_COLOR_ACCENT)
    ax2.tick_params(axis="y", labelcolor=_COLOR_ACCENT)
    # 对齐左右轴零点，记录电量与电费在视觉上保持同一起点
    ax1.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    # 图例二合一（左上角）
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(color=_COLOR_MAIN, alpha=0.8, label="用电量(度)"),
        ax2.get_lines()[0],
    ]
    ax1.legend(handles=legend_handles, loc="upper left")
    fig.tight_layout()
    return fig


def generate_tier_chart(result):
    """生成阶梯费用图：累计电费随用电量增长的阶梯曲线。

    Args:
        result: calculator.calculate() 的返回，含 usage/tiers/total/region。

    Returns:
        Figure: 阶梯折线图，含档位色带与单价标注。
    """
    usage = result.get("usage", 0)
    tiers = result.get("tiers") or []
    total = result.get("total", 0)
    colors = _COLORS

    xs, ys = [], []
    cum_fee = 0.0
    x = 0.0
    for t in tiers:
        if t.get("usage", 0) <= 0:
            continue
        x_end = x + t["usage"]
        fee_end = cum_fee + t["usage"] * t["price"]
        xs.extend([x, x_end])
        ys.extend([cum_fee, fee_end])
        x = x_end
        cum_fee = fee_end

    fig = _new_figure()
    ax = fig.add_subplot(111)

    prev = 0.0
    for idx, t in enumerate(tiers):
        if t.get("usage", 0) <= 0:
            continue
        ax.axvspan(prev, prev + t["usage"],
                   color=colors[idx % len(colors)], alpha=0.10)
        prev += t["usage"]

    ax.plot(xs, ys, drawstyle="steps-post", marker="o",
            color=_COLOR_MAIN, linewidth=2.2, label="累计电费")

    cx, cy = 0.0, 0.0
    for idx, t in enumerate(tiers):
        if t.get("usage", 0) <= 0:
            continue
        cx += t["usage"]
        cy += t["usage"] * t["price"]
        ax.axvline(cx, color="#bbbbbb", linestyle="--", linewidth=1)
        ax.text(cx, cy, f" {t['price']}元/度", fontsize=9,
                color=colors[idx % len(colors)], verticalalignment="bottom")

    ax.axvline(usage, color="#333333", linestyle="-", linewidth=1.4)
    ax.annotate(
        f"总电费 ¥{total:.2f}\n({usage:.0f}度)",
        xy=(usage, total),
        xytext=(usage * 0.45, total * 0.8),
        arrowprops=dict(arrowstyle="->", color="#333333"),
        fontsize=10,
    )

    region = result.get("region", "")
    ax.set_title(f"{region} · 用电 {usage:.0f} 度 · 总电费 ¥{total:.2f}")
    ax.set_xlabel("累计用电量(度)")
    ax.set_ylabel("累计电费(元)")
    ax.grid(True, linestyle="--", alpha=0.4)
    if usage > 0:
        ax.set_xlim(0, usage * 1.15)
    fig.tight_layout()
    return fig


def generate_user_chart(records):
    """生成用户对比图：按用户名聚合总用电量，柱状图对比。

    Args:
        records: 记录列表（按 username 聚合）。

    Returns:
        Figure: 柱状图。
    """
    records = records or []
    if not records:
        return _empty_figure("暂无历史数据")
    agg = {}
    for r in records:
        name = r.get("username") or "匿名"
        a = agg.setdefault(name, [0.0, 0.0])
        a[0] += r.get("usage") or 0
        a[1] += r.get("total") or 0
    names = list(agg)
    usages = [agg[n][0] for n in names]

    fig = _new_figure()
    ax = fig.add_subplot(111)
    ax.bar(names, usages, color=_COLOR_MAIN, alpha=0.85, label="总用电量(度)")
    for x, u in enumerate(usages):
        ax.text(x, u, f"{u:.0f}", ha="center", va="bottom", fontsize=9, color=_COLOR_MAIN)
    ax.set_title("各用户用电量对比")
    ax.set_xlabel("用户")
    ax.set_ylabel("总用电量(度)")
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    if len(names) > 6:
        ax.tick_params(axis="x", rotation=30, labelsize=8)
    fig.tight_layout()
    return fig


def generate_tier_distribution_chart(records):
    """生成档位分布图：按档案用电量所在档位分组，柱状图展示各档记录数与用电总量。

    Args:
        records: 记录列表（使用 current_tier 字段聚合）。

    Returns:
        Figure: 柱状图。
    """
    records = records or []
    if not records:
        return _empty_figure("暂无历史数据")
    agg = {}
    for r in records:
        tier = int(r.get("current_tier") or 0)
        a = agg.setdefault(tier, [0, 0.0])
        a[0] += 1
        a[1] += r.get("usage") or 0
    if not agg:
        return _empty_figure("暂无档位数据")
    items = sorted(agg.items())
    labels = [f"第{t}档" for t, _ in items]
    counts = [v[0] for _, v in items]
    usages = [v[1] for _, v in items]

    fig = _new_figure()
    ax = fig.add_subplot(111)
    x = list(range(len(labels)))
    ax.bar(x, usages, color="#9d7bff", alpha=0.85)
    for xi, (u, c) in enumerate(zip(usages, counts)):
        ax.text(xi, u, f"{u:.0f}度\n{c}条", ha="center", va="bottom", fontsize=9,
                color="#9d7bff")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("用电量档位分布")
    ax.set_xlabel("档位")
    ax.set_ylabel("总用电量(度)")
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    fig.tight_layout()
    return fig


def generate_fee_composition_chart(result):
    """生成电费构成饼图：按当前计算结果的各档费用绘制饼图。

    Args:
        result: calculator.calculate() 的返回，含 total/tiers/usage/region。

    Returns:
        Figure: 饼图。
    """
    usage = result.get("usage", 0)
    tiers = result.get("tiers") or []
    used = [t for t in tiers if t.get("usage", 0) > 0]
    total = result.get("total", 0)
    if not used or total <= 0:
        return _empty_figure("当前用电量未产生电费，无法构成饼图")

    labels = [f"第{t['tier']}档\n{t['amount']:.2f}元" for t in used]
    values = [t["amount"] for t in used]

    fig = _new_figure()
    ax = fig.add_subplot(111)
    ax.pie(
        values, labels=labels, colors=_COLORS[:len(used)],
        autopct="%1.1f%%", startangle=90, textprops={"fontsize": 10},
    )
    ax.axis("equal")
    region = result.get("region", "")
    ax.set_title(f"{region} · 用电 {usage:.0f} 度 · 电费构成 (¥{total:.2f})")
    fig.tight_layout()
    return fig