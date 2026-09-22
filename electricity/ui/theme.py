"""科技感主题 — 集中定义暗色霓虹配色，并应用到全局 ttk 样式。

设计基调：深蓝黑背景 + 青蓝/青绿霓虹强调色，营造冷色科技感。
所有 ui 面板通过本模块统一取色，保证整体风格一致、便于整体换肤。
注意：本模块仅依赖 tkinter，不引入业务逻辑。
"""

import tkinter as tk
from tkinter import ttk

# ── 配色方案（提亮后的清亮科技蓝） ──
BG_DEEP = "#1E2A44"        # 窗口最外层：中深蓝
BG_PANEL = "#2A3A5E"       # 面板/卡片背景
BG_ELEV = "#36486F"        # 输入框/表格等再高一层
BORDER = "#4A5E8C"         # 边框线
BORDER_LIGHT = "#5E76A6"
TEXT_MAIN = "#F1F5FF"      # 主要文字
TEXT_DIM = "#A9B8DC"       # 次要文字
NEON_CYAN = "#00F0FF"      # 主强调：青蓝
NEON_GREEN = "#00FF9D"     # 成功/关键数字：青绿
NEON_VIOLET = "#9D7BFF"    # 次级强调：紫
WARN = "#FFB800"           # 警告
DANGER = "#FF5C5C"         # 危险/异常

FONT_DIGIT = ("Consolas", 16, "bold")   # 关键数字等宽字体
FONT_H1 = ("Microsoft YaHei", 14, "bold")
FONT_BODY = ("Microsoft YaHei", 9)


def apply_theme():
    """配置 clam 主题下的暗色样式，返回 style 对象供调用方使用。"""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # 全局基础
    style.configure(".", background=BG_PANEL, foreground=TEXT_MAIN,
                    font=FONT_BODY, bordercolor=BORDER,
                    lightcolor=BG_PANEL, darkcolor=BG_PANEL,
                    troughcolor=BG_ELEV, fieldbackground=BG_ELEV)

    # 帧与标签
    style.configure("TFrame", background=BG_PANEL)
    style.configure("Root.TFrame", background=BG_DEEP)
    style.configure("TLabel", background=BG_PANEL, foreground=TEXT_MAIN)
    style.configure("Root.TLabel", background=BG_DEEP, foreground=TEXT_MAIN)
    style.configure("Dim.TLabel", foreground=TEXT_DIM)

    # 分组框（卡片）
    style.configure("TLabelframe", background=BG_PANEL, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG_PANEL,
                    foreground=NEON_CYAN, font=FONT_BODY)

    # 输入框
    style.configure("TEntry", fieldbackground=BG_ELEV, foreground=TEXT_MAIN,
                    insertcolor=NEON_CYAN, bordercolor=BORDER, padding=4)
    style.map("TEntry", bordercolor=[("focus", NEON_CYAN)])

    # 下拉框
    style.configure("TCombobox", fieldbackground=BG_ELEV, foreground=TEXT_MAIN,
                    arrowcolor=NEON_CYAN, background=BG_ELEV, bordercolor=BORDER, padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", BG_ELEV)],
              bordercolor=[("focus", NEON_CYAN)])
    root_win = _root_of(style)
    if root_win is not None:
        # 下拉列表弹出层背景
        try:
            root_win.tk.call("ttk::style", "configure", "TCombobox",
                             "-selectbackground", BG_PANEL,
                             "-selectforeground", TEXT_MAIN)
        except tk.TclError:
            pass

    # 普通按钮（暗色描边）
    style.configure("TButton", background=BG_ELEV, foreground=NEON_CYAN,
                    bordercolor=BORDER_LIGHT, padding=4, borderwidth=1)
    style.map("TButton",
              background=[("active", BORDER_LIGHT), ("pressed", BORDER)],
              foreground=[("pressed", NEON_GREEN)])

    # 霓虹主按钮（计算）
    style.configure("Neon.TButton", background="#16608C", foreground="#E6F9FF",
                    bordercolor=NEON_CYAN, padding=(12, 5), borderwidth=1,
                    font=("Microsoft YaHei", 10, "bold"))
    style.map("Neon.TButton",
              background=[("active", "#1D7BB5"), ("pressed", "#0F4A6E")],
              foreground=[("pressed", "#FFFFFF")])

    # 表格整体
    style.configure("Treeview", background=BG_PANEL, fieldbackground=BG_PANEL,
                    foreground=TEXT_MAIN, bordercolor=BORDER, rowheight=26)
    style.map("Treeview",
              background=[("selected", "#143B66")],
              foreground=[("selected", NEON_CYAN)])
    # 表头
    style.configure("Treeview.Heading", background=BG_ELEV,
                    foreground=NEON_CYAN, borderwidth=0, padding=4,
                    font=("Microsoft YaHei", 9, "bold"))
    style.map("Treeview.Heading", background=[("active", BORDER_LIGHT)])

    # 选项卡（Notebook，右侧功能面板）
    style.configure("TNotebook", background=BG_DEEP, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_ELEV, foreground=TEXT_DIM,
                    padding=(12, 6), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", BG_PANEL)],
              foreground=[("selected", NEON_CYAN)])

    # 滚动条
    style.configure("Vertical.TScrollbar", background=BG_ELEV,
                    troughcolor=BG_PANEL, bordercolor=BG_PANEL, arrowcolor=TEXT_DIM)
    style.map("Vertical.TScrollbar", background=[("active", BORDER_LIGHT)])

    return style


def _root_of(style):
    """从 style 反查当前 root，供部分特殊样式兜底；失败返回 None。"""
    try:
        master = style.master
        return master if isinstance(master, tk.Misc) else None
    except Exception:
        return None