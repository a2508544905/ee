"""程序入口 — 创建主窗口并启动事件循环"""

import sys
import os

# 修复：Tcl/Tk 库路径探测
# 有些 Python 安装的 tkinter 找不到 init.tcl（路径错位），
# 需要在 import tkinter 之前显式设置 TCL_LIBRARY / TK_LIBRARY。
def _fix_tcltk_paths():
    if "TCL_LIBRARY" in os.environ and "TK_LIBRARY" in os.environ:
        return  # 已由外部提供，跳过

    base = sys.prefix  # 例如 D:\Python314 或 C:\...\Python314
    local_app = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python")
    candidates = [
        os.path.join(base, "tcl", "tcl8.6"),
        os.path.join(base, "lib", "tcl8.6"),
        os.path.join(base, "..", "tcl", "tcl8.6"),
        os.path.join(local_app, "Python314", "tcl", "tcl8.6"),  # 显式探测本机安装位
    ]
    for cand in candidates:
        init = os.path.join(cand, "init.tcl")
        if os.path.isfile(init):
            os.environ.setdefault("TCL_LIBRARY", cand)
            tk_cand = os.path.join(os.path.dirname(cand), "tk8.6")
            if os.path.isdir(tk_cand):
                os.environ.setdefault("TK_LIBRARY", tk_cand)
            return

    # 兜底：探测常见安装目录下的 tcl
    import glob
    patterns = [
        r"C:\Users\*\AppData\Local\Programs\Python*\tcl\tcl8.6",
        r"D:\Python*\tcl\tcl8.6",
    ]
    for pattern in patterns:
        for p in glob.glob(pattern):
            if os.path.isfile(os.path.join(p, "init.tcl")):
                os.environ.setdefault("TCL_LIBRARY", p)
                tk_cand = os.path.join(os.path.dirname(p), "tk8.6")
                if os.path.isdir(tk_cand):
                    os.environ.setdefault("TK_LIBRARY", tk_cand)
                return


_fix_tcltk_paths()

import tkinter as tk  # noqa: E402

# 确保项目根目录在 sys.path 中，以便导入 ui/lib 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.logger import setup_logger
from ui.main_window import MainWindow


def main():
    setup_logger()
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()