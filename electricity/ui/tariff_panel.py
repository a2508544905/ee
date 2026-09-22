"""档位管理窗口 — 可视化增删改各地区阶梯电价档位，实体操作写回 config/tariffs.json"""

import tkinter as tk
from tkinter import ttk, messagebox

from ui import theme
from ui.theme import apply_theme


class TariffPanel(ttk.Frame):
    """独立弹窗：左侧地区列表，右侧当前地区档位表格 + 编辑表单。"""

    def __init__(self, master, tariff_manager, on_changed=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tariff_manager = tariff_manager
        self.on_changed = on_changed  # 变更后回调（如刷新界面地区下拉）

        self._build_ui()
        self._load_regions()
        self._load_tiers()

    # ── 界面 ──
    def _build_ui(self):
        # 左：地区列表
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 10))
        ttk.Label(left, text="地区", font=("Microsoft YaHei", 10, "bold"),
                  foreground=theme.NEON_CYAN).pack(anchor="w")
        self.region_list = tk.Listbox(
            left, width=12, height=14, bg=theme.BG_ELEV, fg=theme.TEXT_MAIN,
            selectbackground=theme.NEON_CYAN, selectforeground="#001018",
            highlightthickness=0, borderwidth=1, relief="solid",
            activestyle="none",
        )
        self.region_list.pack(fill="y", expand=True, pady=4)
        self.region_list.bind("<<ListboxSelect>>", lambda e: self._load_tiers())

        ttk.Button(left, text="＋ 新增地区", command=self._add_region_popup).pack(fill="x", pady=(2, 0))
        ttk.Button(left, text="🗑 删除地区", command=self._remove_region).pack(fill="x", pady=(2, 0))

        # 右：档位表格 + 编辑区
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        self.tree = ttk.Treeview(
            right, columns=("idx", "min", "max", "price"), show="headings", height=8,
        )
        for key, title, width in (
            ("idx", "档位", 60), ("min", "下限(度)", 90),
            ("max", "上限(度)", 90), ("price", "单价(元/度)", 110),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_tier)
        self.tree.bind("<Double-1>", lambda e: self._load_edit_from_selection())

        # 编辑表单
        form = ttk.LabelFrame(right, text="编辑当前档位", padding=8)
        form.pack(fill="x", pady=(8, 0))

        ttk.Label(form, text="下限(度)").grid(row=0, column=0, sticky="e", padx=4)
        self.min_var = tk.StringVar()
        self.max_var = tk.StringVar()
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.min_var, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(form, text="上限(度)").grid(row=0, column=2, sticky="e", padx=4)
        max_row = ttk.Frame(form)
        max_row.grid(row=0, column=3, padx=4)
        self.max_var.set("")
        self.max_entry = ttk.Entry(max_row, textvariable=self.max_var, width=10)
        self.max_entry.pack(side="left")
        self.no_upper = tk.BooleanVar(value=True)
        ttk.Checkbutton(max_row, text="不限", variable=self.no_upper,
                        command=self._toggle_max).pack(side="left", padx=4)

        ttk.Label(form, text="单价(元)").grid(row=1, column=0, sticky="e", padx=4)
        ttk.Entry(form, textvariable=self.price_var, width=10).grid(row=1, column=1, padx=4)

        ttk.Button(form, text="应用修改", command=self._apply_tier).grid(
            row=1, column=3, padx=4, sticky="w")

        # 操作按钮行
        ops = ttk.Frame(right)
        ops.pack(fill="x", pady=(8, 0))
        ttk.Button(ops, text="＋ 在下方新增档位", command=self._add_tier).pack(side="left")
        ttk.Button(ops, text="− 删除选中档位", command=self._remove_tier).pack(side="left", padx=6)
        ttk.Label(ops, text="修改实时保存到配置文件", foreground=theme.TEXT_DIM,
                  font=("", 8)).pack(side="right")

    # ── 逻辑 ──
    def _toggle_max(self):
        """切换是否“上限不限”，不限时禁用上限输入框。"""
        if self.no_upper.get():
            self.max_entry.configure(state="disabled")
        else:
            self.max_entry.configure(state="normal")

    def _cur_region(self):
        """当前选中的地区名。"""
        sel = self.region_list.curselection()
        return self.region_list.get(sel[0]) if sel else None

    def _load_regions(self):
        """刷新左侧地区列表。"""
        self.region_list.delete(0, tk.END)
        for r in self.tariff_manager.get_regions():
            self.region_list.insert(tk.END, r)
        if self.region_list.size():
            self.region_list.selection_set(0)
            self.region_list.event_generate("<<ListboxSelect>>")

    def _load_tiers(self, *_):
        """把当前地区档位填入表格。"""
        region = self._cur_region()
        self.tree.delete(*self.tree.get_children())
        if not region:
            return
        for i, t in enumerate(self.tariff_manager.get_tiers(region)):
            self.tree.insert("", "end", iid=str(i), values=(
                f"第{i + 1}档", t.get("min", 0), t.get("max") or "不限", t.get("price", 0)))

    def _selected_tier_index(self):
        """表格中选中的档位序号，未选返回 None。"""
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _on_select_tier(self, _e):
        """选中档位时把对应值带入编辑表单。"""
        idx = self._selected_tier_index()
        if idx is None:
            return
        region = self._cur_region()
        t = self.tariff_manager.get_tiers(region)[idx]
        self.min_var.set(_num(t.get("min")))
        self.no_upper.set(t.get("max") is None)
        self._toggle_max()
        self.max_var.set(_num(t.get("max")) if t.get("max") is not None else "")
        self.price_var.set(_num(t.get("price")))

    def _load_edit_from_selection(self):
        """双击表格时也把值带入表单（复用选中逻辑）。"""

    def _read_edit(self):
        """读取表单为 {min, max, price}，非法则抛 ValueError。"""
        min_s = self.min_var.get().strip()
        price_s = self.price_var.get().strip()
        if not min_s or not price_s:
            raise ValueError("下限和单价不能为空")
        tmin = float(min_s)
        price = float(price_s)
        tmax = None if self.no_upper.get() else float(self.max_var.get().strip())
        if tmin < 0:
            raise ValueError("下限不能为负数")
        if price < 0:
            raise ValueError("单价不能为负数")
        if tmax is not None and tmax <= tmin:
            raise ValueError("上限必须大于下限")
        return {"min": tmin, "max": tmax, "price": price}

    def _apply_tier(self):
        """把编辑表单应用到选中的档位（若无选中则新增在最末）。"""
        region = self._cur_region()
        if not region:
            messagebox.showwarning("提示", "请先选择地区")
            return
        try:
            data = self._read_edit()
        except ValueError as exc:
            messagebox.showwarning("输入错误", str(exc))
            return
        idx = self._selected_tier_index()
        if idx is None:
            self.tariff_manager.add_tier(region, data)
        else:
            self.tariff_manager.update_tier(region, idx, data)
        self._load_tiers()
        self._notify_changed(region)

    def _add_tier(self):
        """新增一档：默认取上一档上限作为本档下限，上限不限。"""
        region = self._cur_region()
        if not region:
            messagebox.showwarning("提示", "请先选择地区")
            return
        tiers = self.tariff_manager.get_tiers(region)
        last_max = tiers[-1].get("max") if tiers else None
        new_min = _num(last_max) if last_max is not None else 0.0
        self.tariff_manager.add_tier(region, {"min": new_min, "max": None, "price": 0.0})
        self._load_tiers()
        # 选中新档便于编辑
        last_idx = len(self.tariff_manager.get_tiers(region)) - 1
        self.tree.selection_set(str(last_idx))
        self._on_select_tier(None)
        self._notify_changed(region)

    def _remove_tier(self):
        """删除选中的档位。"""
        region = self._cur_region()
        idx = self._selected_tier_index()
        if not region or idx is None:
            messagebox.showwarning("提示", "请先选择要删除的档位")
            return
        if len(self.tariff_manager.get_tiers(region)) <= 1:
            messagebox.showwarning("提示", "至少保留一档")
            return
        self.tariff_manager.remove_tier(region, idx)
        self._load_tiers()
        self._notify_changed(region)

    def _add_region_popup(self):
        """弹出小窗输入新地区名，添加到配置。"""
        win = tk.Toplevel(self)
        win.title("新增地区")
        win.geometry("240x110")
        win.configure(bg=theme.BG_PANEL)
        ttk.Label(win, text="地区名称：").pack(pady=(14, 4))
        name_var = tk.StringVar()
        ttk.Entry(win, textvariable=name_var, width=20).pack()
        name_var.set("")

        def do_add():
            name = name_var.get().strip()
            if not name:
                return
            if name in self.tariff_manager.get_regions():
                messagebox.showwarning("提示", "该地区已存在")
                return
            self.tariff_manager.add_region(name, [{"min": 0, "max": 200, "price": 0.5}])
            win.destroy()
            self._load_regions()
            self.region_list.selection_set(self.region_list.size() - 1)
            self._load_tiers()
            self._notify_changed(name)

        ttk.Button(win, text="确认", command=do_add).pack(pady=8)

    def _remove_region(self):
        """删除当前地区。"""
        region = self._cur_region()
        if not region:
            messagebox.showwarning("提示", "请先选择地区")
            return
        if not messagebox.askyesno("确认", f"删除地区「{region}」及其全部档位？"):
            return
        self.tariff_manager.remove_region(region)
        self._load_regions()
        self._notify_changed(region)

    def _notify_changed(self, region):
        """通知外部配置已变更（用于刷新主界面地区下拉）。"""
        if self.on_changed:
            self.on_changed(region)


def open_tariff_window(master, tariff_manager, on_changed=None):
    """创建并显示档位管理窗口。"""
    win = tk.Toplevel(master)
    win.title("档位规则管理")
    win.geometry("640x420")
    win.minsize(560, 360)
    win.configure(bg=theme.BG_DEEP)
    apply_theme()
    panel = TariffPanel(win, tariff_manager, on_changed=on_changed)
    panel.pack(fill="both", expand=True, padx=12, pady=12)
    return win


def _num(value):
    """数字转去尾零字符串。"""
    if value is None:
        return ""
    return f"{value:g}"