"""预留功能区：用 Notebook 占位后续要加入的功能"""

from tkinter import ttk


class MorePanel(ttk.LabelFrame):
    """右侧预留区，用选项卡占位未来功能（导入/导出/图表）。

    当前只放占位说明，后续功能实现时在对应 tab 中填充。
    """

    # 未来的功能 tab：(tab标题, 占位提示)
    TABS = [
        ("CSV 导入", "CSV 导入功能即将上线\n（从文件读取用电量列表）"),
        ("导出", "导出功能即将上线\n（将记录导出为 Excel/CSV）"),
        ("统计图表", "图表功能即将上线\n（matplotlib 趋势图、阶梯面积图）"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, text="更多功能", padding=8, **kwargs)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        for title, hint in self.TABS:
            page = ttk.Frame(self.notebook, padding=20)
            self.notebook.add(page, text=title)
            ttk.Label(
                page, text=hint, justify="center", anchor="center",
                foreground="#888888", wraplength=180,
            ).pack(fill="both", expand=True)

    def add_tab(self, title, frame):
        """动态追加一个新功能 tab。"""
        self.notebook.add(frame, text=title)