#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 万能工具箱 - 桌面 GUI 应用
基于 PyMuPDF · 纯本地处理 · 无需联网
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import List, Optional
from core import (
    merge_pdfs, compress_pdf, add_watermark, pdf_to_images,
    get_pdf_page_count, get_file_size_str, word_to_pdf, is_word_file,
)

# ── 常量 ──────────────────────────────────────────────────────────
APP_TITLE = "📄 PDF 萬能工具箱"
APP_SUBTITLE = "純本地處理 · 無需上傳 · 安全可靠"
WINDOW_SIZE = "820x720"
COLOR_PRIMARY = "#2563eb"
COLOR_PRIMARY_HOVER = "#1d4ed8"
COLOR_BG = "#f0f4f8"
COLOR_SURFACE = "#ffffff"
COLOR_TEXT = "#1e293b"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_BORDER = "#e2e8f0"
COLOR_SUCCESS = "#10b981"
COLOR_ERROR = "#ef4444"

FONT_FAMILY = "Microsoft YaHei UI"
FONT_SIZE = 10


# ── 工具定义 ──────────────────────────────────────────────────────
class ToolInfo:
    def __init__(self, key: str, label: str, icon: str, desc: str, single_file: bool):
        self.key = key
        self.label = label
        self.icon = icon
        self.desc = desc
        self.single_file = single_file


TOOLS = [
    ToolInfo("merge",     "合併 PDF",     "📄", "多個 PDF 合併為一個",    False),
    ToolInfo("compress",  "壓縮 PDF",     "📦", "最佳化減小 PDF 大小",    True),
    ToolInfo("watermark", "新增浮水印",   "💧", "自訂文字浮水印",         True),
    ToolInfo("toimage",   "PDF 轉圖片",   "🖼️", "PDF 每頁轉為圖片",       True),
    ToolInfo("wordtopdf", "WPS 轉 PDF",   "📝", "WPS/Word 文件轉為 PDF", True),
]


# ── 主应用 ─────────────────────────────────────────────────────────
class PDFToolboxApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(700, 620)
        self.root.configure(bg=COLOR_BG)

        # 状态
        self.files: List[str] = []
        self.active_tool: Optional[str] = None
        self.processing = False
        # 合併用：索引順序與勾選狀態（僅 merge tool 使用）
        self.merge_order: List[int] = []       # self.files 的索引，表示合併順序
        self.merge_checked: List[bool] = []    # 對應 merge_order，True=勾選

        self._setup_styles()
        self._build_ui()

        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

    # ── 样式 ──────────────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_SURFACE, relief="flat", borderwidth=0)
        style.configure("Header.TLabel",
                        background=COLOR_BG, foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, 22, "bold"))
        style.configure("Subtitle.TLabel",
                        background=COLOR_BG, foreground=COLOR_TEXT_SECONDARY,
                        font=(FONT_FAMILY, 10))
        style.configure("Section.TLabel",
                        background=COLOR_BG, foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, 12, "bold"))
        style.configure("CardTitle.TLabel",
                        background=COLOR_SURFACE, foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, 11, "bold"))
        style.configure("Body.TLabel",
                        background=COLOR_SURFACE, foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, FONT_SIZE))
        style.configure("BodyDim.TLabel",
                        background=COLOR_SURFACE, foreground=COLOR_TEXT_SECONDARY,
                        font=(FONT_FAMILY, 9))
        style.configure("Success.TLabel",
                        background=COLOR_SURFACE, foreground=COLOR_SUCCESS,
                        font=(FONT_FAMILY, 13, "bold"))
        style.configure("Error.TLabel",
                        background=COLOR_SURFACE, foreground=COLOR_ERROR,
                        font=(FONT_FAMILY, 13, "bold"))
        style.configure("Footer.TLabel",
                        background=COLOR_BG, foreground=COLOR_TEXT_SECONDARY,
                        font=(FONT_FAMILY, 9))
        style.configure("Tool.TFrame", background=COLOR_SURFACE, relief="solid", borderwidth=0)

    # ── 构建 UI ───────────────────────────────────────────────────
    def _build_ui(self):
        # 主容器
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=16)

        # ── 头部 ──
        self._build_header()

        # ── 文件区 ──
        self._build_file_section()

        # ── 工具区 ──
        self._build_tool_section()

        # ── 选项面板 ──
        self._build_options_section()

        # ── 结果面板 ──
        self._build_result_section()

        # ── 底部 ──
        self._build_footer()

    def _build_header(self):
        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text=APP_TITLE, style="Header.TLabel").pack()
        ttk.Label(header, text=APP_SUBTITLE, style="Subtitle.TLabel").pack()

    def _build_file_section(self):
        """文件管理区域"""
        card = ttk.Frame(self.main_frame, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 12))
        # 圆角效果用 padding 模拟
        inner = tk.Frame(card, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                         highlightthickness=1, padx=16, pady=12)
        inner.pack(fill="x", padx=1, pady=1)

        # 标题行
        title_row = tk.Frame(inner, bg=COLOR_SURFACE)
        title_row.pack(fill="x", pady=(0, 8))
        tk.Label(title_row, text="📂 PDF 檔案列表",
                 font=(FONT_FAMILY, 12, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(side="left")

        self.file_count_label = tk.Label(title_row, text="(0 個檔案)",
                                          font=(FONT_FAMILY, 10), bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY)
        self.file_count_label.pack(side="left", padx=(8, 0))

        tk.Button(title_row, text="🗁 新增檔案", font=(FONT_FAMILY, 9),
                  bg=COLOR_PRIMARY, fg="white", relief="flat", padx=12, pady=2,
                  activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                  cursor="hand2", command=self._on_add_files).pack(side="right", padx=(4, 0))
        tk.Button(title_row, text="清空", font=(FONT_FAMILY, 9),
                  bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, relief="flat", padx=8, pady=2,
                  activebackground="#f1f5f9", cursor="hand2",
                  command=self._on_clear_files).pack(side="right")

        # 文件列表容器
        self.file_list_frame = tk.Frame(inner, bg=COLOR_SURFACE)
        self.file_list_frame.pack(fill="x")
        self._refresh_file_list()

    def _refresh_file_list(self):
        """刷新文件列表 UI"""
        for w in self.file_list_frame.winfo_children():
            w.destroy()

        if not self.files:
            empty = tk.Label(self.file_list_frame,
                             text="還沒有新增檔案，點擊上方按鈕新增 PDF",
                             font=(FONT_FAMILY, 10), bg=COLOR_SURFACE, fg="#94a3b8",
                             pady=20)
            empty.pack(fill="x")
        else:
            for idx, path in enumerate(self.files):
                self._create_file_row(idx, path)

        self.file_count_label.config(text=f"({len(self.files)} 個檔案)")

    def _create_file_row(self, idx: int, path: str):
        """创建单个文件行"""
        name = os.path.basename(path)
        size = get_file_size_str(os.path.getsize(path))
        pages = get_pdf_page_count(path)
        meta = f"{size}"
        if pages:
            meta += f" · {pages} 頁"

        row = tk.Frame(self.file_list_frame, bg=COLOR_SURFACE, padx=8, pady=4)
        row.pack(fill="x")

        # 拖拽序号
        tk.Label(row, text=f"  {idx + 1}.", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, width=3).pack(side="left")
        # 文件名
        tk.Label(row, text=name, font=(FONT_FAMILY, 10, "bold"),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, anchor="w", width=40).pack(side="left", padx=(4, 0))
        # 元信息
        tk.Label(row, text=meta, font=(FONT_FAMILY, 9),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY).pack(side="left", padx=(8, 0))
        # 删除按钮
        btn_del = tk.Button(row, text="✕", font=(FONT_FAMILY, 8),
                            bg=COLOR_SURFACE, fg="#94a3b8", relief="flat",
                            padx=6, pady=0, cursor="hand2",
                            activebackground="#fee2e2", activeforeground=COLOR_ERROR,
                            command=lambda i=idx: self._on_remove_file(i))
        btn_del.pack(side="right")

    def _on_add_files(self):
        files = filedialog.askopenfilenames(
            title="選擇 PDF 檔案",
            filetypes=[("PDF 檔案", "*.pdf"), ("所有檔案", "*.*")]
        )
        added = False
        for f in files:
            if f not in self.files and f.lower().endswith('.pdf'):
                self.files.append(f)
                added = True
        if not added:
            return
        self._refresh_file_list()
        self._hide_result()
        self._rebuild_merge_state()
        # 預設選定合併工具
        self._on_tool_select("merge")

    def _on_remove_file(self, idx: int):
        self.files.pop(idx)
        self._refresh_file_list()
        self._rebuild_merge_state()
        # 如果還在合併面板就刷新
        if self.active_tool == "merge":
            self._switch_options("merge")

    def _on_clear_files(self):
        self.files.clear()
        self.active_tool = None
        self.merge_order.clear()
        self.merge_checked.clear()
        self._refresh_file_list()
        self._hide_result()
        # 清除工具按鈕高亮
        for btn in self.tool_buttons.values():
            btn.configure(highlightbackground=COLOR_BORDER, highlightthickness=1)
            for c in btn.winfo_children():
                c.configure(bg=COLOR_SURFACE)
        # 重置選項面板回到提示狀態
        for w in self.options_content.winfo_children():
            w.destroy()
        ttk.Label(self.options_content, text="請先上傳檔案，然後選擇一個工具",
                  style="BodyDim.TLabel").pack(pady=(12, 4))

    def _rebuild_merge_state(self):
        """根據目前 self.files 重建合併順序與勾選狀態"""
        old_order = self.merge_order[:] if hasattr(self, 'merge_order') else []
        old_checked = self.merge_checked[:] if hasattr(self, 'merge_checked') else []

        n = len(self.files)
        self.merge_order = []
        self.merge_checked = []

        # 保留舊順序中仍存在的檔案
        for idx in old_order:
            if idx < n:
                self.merge_order.append(idx)
                checked = old_checked[len(self.merge_order) - 1] if len(self.merge_order) - 1 < len(old_checked) else True
                self.merge_checked.append(checked)

        # 新增不在舊順序中的檔案（附加在最後）
        existing = set(self.merge_order)
        for i in range(n):
            if i not in existing:
                self.merge_order.append(i)
                self.merge_checked.append(True)

    # ── 工具区 ────────────────────────────────────────────────────
    def _build_tool_section(self):
        """五個工具按鈕（分兩行）"""
        card = ttk.Frame(self.main_frame, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(card, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                         highlightthickness=1, padx=16, pady=12)
        inner.pack(fill="x", padx=1, pady=1)

        tk.Label(inner, text="⚙️ 選擇工具",
                 font=(FONT_FAMILY, 12, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(anchor="w")

        # 第一行：合併、壓縮、浮水印
        row1 = tk.Frame(inner, bg=COLOR_SURFACE)
        row1.pack(fill="x", pady=(8, 4))
        # 第二行：轉圖片、Word 轉 PDF
        row2 = tk.Frame(inner, bg=COLOR_SURFACE)
        row2.pack(fill="x")

        self.tool_buttons = {}
        rows = [row1, row1, row1, row2, row2]  # 前 3 個放 row1，後 2 個放 row2
        for i, tool in enumerate(TOOLS):
            btn = self._create_tool_button(rows[i], tool)
            self.tool_buttons[tool.key] = btn

    def _create_tool_button(self, parent, tool: ToolInfo):
        """创建单个工具按钮"""
        btn = tk.Frame(parent, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                       highlightthickness=1, cursor="hand2", padx=12, pady=8)
        btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        icon_lbl = tk.Label(btn, text=tool.icon, font=(FONT_FAMILY, 20),
                            bg=COLOR_SURFACE, fg=COLOR_TEXT)
        icon_lbl.pack()
        name_lbl = tk.Label(btn, text=tool.label, font=(FONT_FAMILY, 11, "bold"),
                            bg=COLOR_SURFACE, fg=COLOR_TEXT)
        name_lbl.pack()
        desc_lbl = tk.Label(btn, text=tool.desc, font=(FONT_FAMILY, 8),
                            bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY)
        desc_lbl.pack()

        # 绑定点击事件
        for widget in (btn, icon_lbl, name_lbl, desc_lbl):
            widget.bind("<Button-1>", lambda e, k=tool.key: self._on_tool_select(k))
            widget.bind("<Enter>", lambda e, b=btn: self._on_tool_hover(b, True))
            widget.bind("<Leave>", lambda e, b=btn: self._on_tool_hover(b, False))

        return btn

    def _on_tool_hover(self, frame, entering: bool):
        if entering:
            frame.configure(bg="#f8fafc")
            for c in frame.winfo_children():
                c.configure(bg="#f8fafc")
        else:
            frame.configure(bg=COLOR_SURFACE)
            for c in frame.winfo_children():
                c.configure(bg=COLOR_SURFACE)

    def _on_tool_select(self, key: str):
        if self.processing:
            return
        self.active_tool = key
        self._hide_result()

        # 高亮选中按钮
        for k, btn in self.tool_buttons.items():
            highlight = COLOR_PRIMARY if k == key else COLOR_BORDER
            bg = "#eef2ff" if k == key else COLOR_SURFACE
            btn.configure(highlightbackground=highlight, highlightthickness=2 if k == key else 1)
            for c in btn.winfo_children():
                c.configure(bg=bg)

        # 切换选项面板
        self._switch_options(key)

    def _switch_options(self, tool_key: str):
        """根据选中的工具切换选项面板"""
        for w in self.options_content.winfo_children():
            w.destroy()

        # 显示对应的选项
        switch = {
            "merge": self._show_merge_options,
            "compress": self._show_compress_options,
            "watermark": self._show_watermark_options,
            "toimage": self._show_toimage_options,
            "wordtopdf": self._show_wordtopdf_options,
        }
        show_fn = switch.get(tool_key)
        if show_fn:
            show_fn()

    # ── 选项面板 ──────────────────────────────────────────────────
    def _build_options_section(self):
        """选项配置区域（动态切换）"""
        card = ttk.Frame(self.main_frame, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 12))
        self.options_inner = tk.Frame(card, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                                      highlightthickness=1, padx=16, pady=12)
        self.options_inner.pack(fill="x", padx=1, pady=1)

        tk.Label(self.options_inner, text="🔧 參數配置",
                 font=(FONT_FAMILY, 12, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(anchor="w")

        self.options_content = tk.Frame(self.options_inner, bg=COLOR_SURFACE)
        self.options_content.pack(fill="x", pady=(8, 0))

        # 初始：提示
        ttk.Label(self.options_content, text="請先在左側上傳檔案，然後選擇一個工具",
                  style="BodyDim.TLabel").pack(pady=(12, 4))

    def _show_merge_options(self):
        """合併選項 — 可勾選與排序檔案"""
        self._rebuild_merge_state()
        n = len(self.files)
        if n == 0:
            ttk.Label(self.options_content, text="請先上傳 PDF 檔案",
                      style="BodyDim.TLabel").pack(pady=(12, 4))
            return

        # 標題資訊
        info_frame = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        info_frame.pack(fill="x", pady=(0, 8))
        tk.Label(info_frame, text=f"共 {n} 個檔案，已勾選 {sum(self.merge_checked)} 個",
                 font=(FONT_FAMILY, 10), bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY).pack(side="left")

        # 全選 / 取消全選
        def toggle_all():
            new_val = not all(self.merge_checked)
            for i in range(len(self.merge_checked)):
                self.merge_checked[i] = new_val
            self._switch_options("merge")

        tk.Button(info_frame, text="全選/取消", font=(FONT_FAMILY, 8),
                  bg=COLOR_SURFACE, fg=COLOR_PRIMARY, relief="flat", padx=8, pady=0,
                  cursor="hand2", command=toggle_all).pack(side="right")

        # 可滾動的檔案列表
        canvas_frame = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        canvas_frame.pack(fill="x", pady=(0, 8))

        canvas = tk.Canvas(canvas_frame, bg=COLOR_SURFACE, highlightthickness=0,
                           height=min(n * 44, 220))
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        list_frame = tk.Frame(canvas, bg=COLOR_SURFACE)

        list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=list_frame, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 顯示檔案行（依 merge_order）
        for pos, idx in enumerate(self.merge_order):
            path = self.files[idx]
            name = os.path.basename(path)
            size = get_file_size_str(os.path.getsize(path))
            pages = get_pdf_page_count(path)
            meta = f"{size}"
            if pages:
                meta += f" · {pages} 頁"

            row = tk.Frame(list_frame, bg=COLOR_SURFACE, padx=4, pady=2)
            row.pack(fill="x")

            # 勾選框
            checked = tk.BooleanVar(value=self.merge_checked[pos])
            cb = tk.Checkbutton(row, variable=checked, bg=COLOR_SURFACE,
                                fg=COLOR_TEXT, selectcolor=COLOR_SURFACE,
                                command=lambda p=pos, v=checked: self._on_merge_check(p, v))
            cb.pack(side="left")

            # 序號
            tk.Label(row, text=f"{pos+1}.", font=(FONT_FAMILY, 10),
                     bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, width=3).pack(side="left")

            # 檔名
            tk.Label(row, text=name, font=(FONT_FAMILY, 10),
                     bg=COLOR_SURFACE, fg=COLOR_TEXT, anchor="w", width=38).pack(side="left", padx=(2, 0))

            # 大小資訊
            tk.Label(row, text=meta, font=(FONT_FAMILY, 8),
                     bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, width=16).pack(side="left")

            # ▲ 上移按鈕
            if pos > 0:
                btn_up = tk.Button(row, text="▲", font=(FONT_FAMILY, 7),
                                   bg=COLOR_SURFACE, fg="#94a3b8", relief="flat",
                                   padx=4, pady=0, cursor="hand2",
                                   activebackground="#eef2ff", activeforeground=COLOR_PRIMARY,
                                   command=lambda p=pos: self._merge_move(p, -1))
                btn_up.pack(side="right", padx=(1, 0))

            # ▼ 下移按鈕
            if pos < len(self.merge_order) - 1:
                btn_dn = tk.Button(row, text="▼", font=(FONT_FAMILY, 7),
                                   bg=COLOR_SURFACE, fg="#94a3b8", relief="flat",
                                   padx=4, pady=0, cursor="hand2",
                                   activebackground="#eef2ff", activeforeground=COLOR_PRIMARY,
                                   command=lambda p=pos: self._merge_move(p, 1))
                btn_dn.pack(side="right", padx=(1, 0))

            # 分隔線
            tk.Frame(list_frame, bg=COLOR_BORDER, height=1).pack(fill="x")

        if n > 5:
            scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="x", expand=True)

        checked_count = sum(self.merge_checked)
        self._show_process_btn(
            f"合併已勾選的 {checked_count} 個檔案" if checked_count < n else f"開始合併全部 {n} 個檔案",
            self._do_merge
        )

    # ── 合併輔助方法 ────────────────────────────────────────────
    def _on_merge_check(self, pos: int, var: tk.BooleanVar):
        """合併檔案勾選狀態變更"""
        if pos < len(self.merge_checked):
            self.merge_checked[pos] = var.get()
            # 更新按鈕文字
            n = len(self.files)
            checked_count = sum(self.merge_checked)
            if hasattr(self, 'process_btn') and self.process_btn.winfo_exists():
                if checked_count < n:
                    self.process_btn.config(text=f"合併已勾選的 {checked_count} 個檔案")
                else:
                    self.process_btn.config(text=f"開始合併全部 {n} 個檔案")

    def _merge_move(self, pos: int, direction: int):
        """移動合併順序：direction= -1 上移，+1 下移"""
        new_pos = pos + direction
        if new_pos < 0 or new_pos >= len(self.merge_order):
            return
        # 交換 merge_order 與 merge_checked
        self.merge_order[pos], self.merge_order[new_pos] = self.merge_order[new_pos], self.merge_order[pos]
        self.merge_checked[pos], self.merge_checked[new_pos] = self.merge_checked[new_pos], self.merge_checked[pos]
        # 刷新面板
        self._switch_options("merge")

    # ──────────────────────────────────────────────────────────────
    def _show_compress_options(self):
        """壓縮選項"""
        tk.Label(self.options_content, text="壓縮程度",
                 font=(FONT_FAMILY, 10), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(anchor="w")
        self.compress_var = tk.DoubleVar(value=0.6)
        scale = tk.Scale(self.options_content, from_=0.1, to=1.0, resolution=0.1,
                         orient="horizontal", length=300, variable=self.compress_var,
                         bg=COLOR_SURFACE, fg=COLOR_TEXT, highlightthickness=0,
                         font=(FONT_FAMILY, 9), showvalue=False)
        scale.pack(fill="x", pady=(4, 0))
        # 标签
        lbl_frame = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        lbl_frame.pack(fill="x")
        tk.Label(lbl_frame, text="← 更小", font=(FONT_FAMILY, 8),
                 bg=COLOR_SURFACE, fg="#94a3b8").pack(side="left")
        self.compress_value_label = tk.Label(lbl_frame, text="0.6 (推薦)",
                                              font=(FONT_FAMILY, 9), bg=COLOR_SURFACE, fg=COLOR_TEXT)
        self.compress_value_label.pack(side="right")

        def on_compress_change(v):
            val = float(v)
            if val <= 0.3:
                tag = "最大壓縮"
            elif val <= 0.6:
                tag = "推薦"
            else:
                tag = "輕度壓縮"
            self.compress_value_label.config(text=f"{val:.1f} ({tag})")
        scale.configure(command=on_compress_change)

        # 原始大小提示
        if self.files:
            orig = get_file_size_str(os.path.getsize(self.files[0]))
            ttk.Label(self.options_content, text=f"原始大小: {orig}",
                      style="BodyDim.TLabel").pack(anchor="w", pady=(4, 0))

        self._show_process_btn("開始壓縮", self._do_compress)

    def _show_watermark_options(self):
        """浮水印選項"""
        opts = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        opts.pack(fill="x")

        # 浮水印文字
        row1 = tk.Frame(opts, bg=COLOR_SURFACE)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="浮水印文字", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_text_var = tk.StringVar(value="CONFIDENTIAL")
        tk.Entry(row1, textvariable=self.wm_text_var, font=(FONT_FAMILY, 10),
                 bg="#f8fafc", fg=COLOR_TEXT, relief="solid", bd=1).pack(side="left", fill="x", expand=True)

        # 字型大小 + 透明度
        row2 = tk.Frame(opts, bg=COLOR_SURFACE)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="字型大小", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_fontsize_var = tk.IntVar(value=48)
        tk.Scale(row2, from_=12, to=120, orient="horizontal", length=150,
                 variable=self.wm_fontsize_var, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 highlightthickness=0, font=(FONT_FAMILY, 8)).pack(side="left")
        tk.Label(opts, text="", width=2, bg=COLOR_SURFACE).pack()

        row2b = tk.Frame(opts, bg=COLOR_SURFACE)
        row2b.pack(fill="x", pady=4)
        tk.Label(row2b, text="透明度", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_opacity_var = tk.DoubleVar(value=0.4)
        tk.Scale(row2b, from_=0.05, to=1.0, resolution=0.05, orient="horizontal",
                 length=150, variable=self.wm_opacity_var, bg=COLOR_SURFACE,
                 fg=COLOR_TEXT, highlightthickness=0, font=(FONT_FAMILY, 8)).pack(side="left")

        # 旋转 + 颜色
        row3 = tk.Frame(opts, bg=COLOR_SURFACE)
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="旋轉角度", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_rotation_var = tk.IntVar(value=-30)
        tk.Scale(row3, from_=-180, to=180, orient="horizontal", length=150,
                 variable=self.wm_rotation_var, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 highlightthickness=0, font=(FONT_FAMILY, 8)).pack(side="left")

        row3b = tk.Frame(opts, bg=COLOR_SURFACE)
        row3b.pack(fill="x", pady=4)
        tk.Label(row3b, text="顏色", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_color_var = tk.StringVar(value="#CCCCCC")
        color_btn = tk.Button(row3b, text="選擇顏色", font=(FONT_FAMILY, 9),
                              bg=self.wm_color_var.get(), relief="solid", bd=1,
                              padx=12, pady=2, cursor="hand2",
                              command=self._pick_watermark_color)
        color_btn.pack(side="left")
        # 颜色预览方块
        self.wm_color_preview = tk.Canvas(row3b, width=24, height=24,
                                          bg=COLOR_SURFACE, bd=1, relief="solid",
                                          highlightthickness=0)
        self.wm_color_preview.pack(side="left", padx=(8, 0))
        self.wm_color_preview.create_rectangle(2, 2, 22, 22, fill="#CCCCCC", outline="")

        # 位置
        row4 = tk.Frame(opts, bg=COLOR_SURFACE)
        row4.pack(fill="x", pady=4)
        tk.Label(row4, text="位置", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.wm_position_var = tk.StringVar(value="center")
        pos_menu = ttk.Combobox(row4, textvariable=self.wm_position_var,
                                values=["center", "top-left", "top-right", "bottom-left", "bottom-right", "tile"],
                                state="readonly", width=18, font=(FONT_FAMILY, 10))
        pos_menu.pack(side="left")
        pos_menu.bind("<<ComboboxSelected>>", lambda e: None)

        self._show_process_btn("新增浮水印", self._do_watermark)

    def _pick_watermark_color(self):
        color = colorchooser.askcolor(title="選擇浮水印顏色", initialcolor=self.wm_color_var.get())
        if color and color[1]:
            self.wm_color_var.set(color[1])
            self.wm_color_preview.create_rectangle(2, 2, 22, 22, fill=color[1], outline="")

    def _show_toimage_options(self):
        """轉圖片選項"""
        opts = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        opts.pack(fill="x")

        row1 = tk.Frame(opts, bg=COLOR_SURFACE)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="圖片格式", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.img_format_var = tk.StringVar(value="png")
        fmt_menu = ttk.Combobox(row1, textvariable=self.img_format_var,
                                values=["png", "jpeg", "webp"],
                                state="readonly", width=10, font=(FONT_FAMILY, 10))
        fmt_menu.pack(side="left")

        row2 = tk.Frame(opts, bg=COLOR_SURFACE)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="縮放倍數", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.img_scale_var = tk.IntVar(value=2)
        for val, label in [(1, "1x (72 DPI)"), (2, "2x (144 DPI)"),
                           (3, "3x (216 DPI)"), (4, "4x (288 DPI)")]:
            tk.Radiobutton(row2, text=label, variable=self.img_scale_var, value=val,
                           bg=COLOR_SURFACE, fg=COLOR_TEXT, selectcolor=COLOR_SURFACE,
                           font=(FONT_FAMILY, 9)).pack(side="left", padx=(0, 8))

        # 品质（仅 JPEG/WebP）
        self.img_quality_frame = tk.Frame(opts, bg=COLOR_SURFACE)
        self.img_quality_frame.pack(fill="x", pady=(4, 0))
        row3 = tk.Frame(self.img_quality_frame, bg=COLOR_SURFACE)
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="圖片品質", font=(FONT_FAMILY, 10),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT, width=12, anchor="w").pack(side="left")
        self.img_quality_var = tk.IntVar(value=90)
        self.img_quality_label = tk.Label(row3, text="90%",
                                           font=(FONT_FAMILY, 9), bg=COLOR_SURFACE, fg=COLOR_TEXT)
        self.img_quality_label.pack(side="right", padx=(8, 0))

        def on_q_change(v):
            self.img_quality_label.config(text=f"{int(float(v))}%")

        tk.Scale(row3, from_=10, to=100, orient="horizontal", length=200,
                 variable=self.img_quality_var, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 highlightthickness=0, font=(FONT_FAMILY, 8), showvalue=False,
                 command=on_q_change).pack(side="left", fill="x", expand=True)

        self._show_process_btn("開始轉換", self._do_toimage)

    def _show_option_hint(self, text: str):
        ttk.Label(self.options_content, text=text,
                  style="Body.TLabel").pack(anchor="w", pady=(4, 0))

    def _show_process_btn(self, label: str, command):
        """显示处理按钮"""
        btn_frame = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        btn_frame.pack(fill="x", pady=(12, 0))
        self.process_btn = tk.Button(btn_frame, text=f"▶  {label}",
                                      font=(FONT_FAMILY, 12, "bold"),
                                      bg=COLOR_PRIMARY, fg="white", relief="flat",
                                      padx=24, pady=8, cursor="hand2",
                                      activebackground=COLOR_PRIMARY_HOVER,
                                      activeforeground="white",
                                      command=command)
        self.process_btn.pack()

    # ── 结果面板 ──────────────────────────────────────────────────
    def _build_result_section(self):
        """结果展示区域"""
        card = ttk.Frame(self.main_frame, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 12))
        self.result_inner = tk.Frame(card, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                                     highlightthickness=1, padx=16, pady=12)
        self.result_inner.pack(fill="x", padx=1, pady=1)

        tk.Label(self.result_inner, text="📊 處理狀態",
                 font=(FONT_FAMILY, 12, "bold"), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(anchor="w")

        self.result_content = tk.Frame(self.result_inner, bg=COLOR_SURFACE)
        self.result_content.pack(fill="x", pady=(8, 0))

        # 初始状态
        self._show_idle()

    def _show_idle(self):
        """空闲状态"""
        for w in self.result_content.winfo_children():
            w.destroy()
        ttk.Label(self.result_content,
                  text="選擇一個工具並配置參數後，點擊處理按鈕開始",
                  style="BodyDim.TLabel").pack(pady=(12, 4))

    def _show_processing(self, message: str, progress: int = 0):
        """处理中状态"""
        for w in self.result_content.winfo_children():
            w.destroy()
        frame = tk.Frame(self.result_content, bg=COLOR_SURFACE)
        frame.pack(fill="x", pady=(8, 4))

        # 转圈动画用文字替代
        tk.Label(frame, text="⏳ 處理中...",
                 font=(FONT_FAMILY, 11, "bold"), bg=COLOR_SURFACE, fg=COLOR_PRIMARY).pack()
        ttk.Label(frame, text=message, style="BodyDim.TLabel").pack(pady=(4, 8))

        # 简单进度条
        self.progress_bar = tk.Canvas(frame, height=8, bg=COLOR_BORDER, bd=0,
                                      highlightthickness=0)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self._update_progress(progress)

    def _update_progress(self, pct: int):
        if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            w = self.progress_bar.winfo_width()
            if w > 1:
                self.progress_bar.delete("all")
                self.progress_bar.create_rectangle(0, 0, int(w * pct / 100), 8,
                                                   fill=COLOR_PRIMARY, outline="")

    def _show_success(self, message: str, output_path: Optional[str] = None):
        """成功状态"""
        for w in self.result_content.winfo_children():
            w.destroy()
        frame = tk.Frame(self.result_content, bg=COLOR_SURFACE)
        frame.pack(fill="x", pady=(8, 4))

        tk.Label(frame, text="✅ 處理完成！",
                 font=(FONT_FAMILY, 14, "bold"), bg=COLOR_SURFACE, fg=COLOR_SUCCESS).pack()
        ttk.Label(frame, text=message, style="Body.TLabel").pack(pady=(4, 0))

        if output_path:
            btn = tk.Button(frame, text=f"📁 開啟檔案所在位置",
                            font=(FONT_FAMILY, 10), bg="#f0fdf4", fg=COLOR_SUCCESS,
                            relief="flat", padx=16, pady=4, cursor="hand2",
                            command=lambda: self._open_output_location(output_path))
            btn.pack(pady=(8, 0))

            btn2 = tk.Button(frame, text=f"📂 在檔案總管中顯示",
                             font=(FONT_FAMILY, 9), bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY,
                             relief="flat", padx=12, pady=2, cursor="hand2",
                             command=lambda: self._explorer_show(output_path))
            btn2.pack(pady=(0, 4))

        self._show_continue_btn()

    def _show_error(self, message: str):
        """错误状态"""
        for w in self.result_content.winfo_children():
            w.destroy()
        frame = tk.Frame(self.result_content, bg=COLOR_SURFACE)
        frame.pack(fill="x", pady=(8, 4))

        tk.Label(frame, text="❌ 處理失敗",
                 font=(FONT_FAMILY, 14, "bold"), bg=COLOR_SURFACE, fg=COLOR_ERROR).pack()
        ttk.Label(frame, text=message, style="Body.TLabel").pack(pady=(4, 0))
        self._show_continue_btn()

    def _show_continue_btn(self):
        btn_frame = tk.Frame(self.result_content, bg=COLOR_SURFACE)
        btn_frame.pack(fill="x", pady=(8, 0))
        tk.Button(btn_frame, text="繼續處理", font=(FONT_FAMILY, 10),
                  bg=COLOR_SURFACE, fg=COLOR_TEXT_SECONDARY, relief="solid", bd=1,
                  padx=16, pady=4, cursor="hand2",
                  command=self._on_continue).pack()

    def _on_continue(self):
        self._hide_result()

    def _hide_result(self):
        self._show_idle()

    def _open_output_location(self, path: str):
        """打开输出文件位置"""
        os.startfile(os.path.dirname(path))

    def _explorer_show(self, path: str):
        """在资源管理器中高亮文件"""
        os.startfile(path)

    # ── 底部 ──────────────────────────────────────────────────────
    def _build_footer(self):
        ttk.Label(self.main_frame, text="基於 PyMuPDF · 純本地桌面應用 · 所有處理在您自己的電腦上完成",
                  style="Footer.TLabel").pack(pady=(4, 0))

    # ── 处理逻辑 ──────────────────────────────────────────────────
    def _do_merge(self):
        if self.processing:
            return

        # 收集勾選的檔案（依 merge_order 順序）
        self._rebuild_merge_state()
        selected = []
        for pos, idx in enumerate(self.merge_order):
            if pos < len(self.merge_checked) and self.merge_checked[pos]:
                selected.append(self.files[idx])

        if len(selected) < 2:
            messagebox.showwarning("提示", "合併至少需要勾選 2 個 PDF 檔案")
            return

        output = filedialog.asksaveasfilename(
            title="儲存合併後的 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")]
        )
        if not output:
            return

        self._start_processing()
        self._show_processing("正在合併 PDF...")

        def run():
            try:
                merge_pdfs(selected, output)
                self.root.after(0, lambda: self._finish_success(
                    f"成功合併 {len(selected)} 個檔案", output))
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _do_compress(self):
        if self.processing:
            return
        if not self.files:
            messagebox.showwarning("提示", "請先新增 PDF 檔案")
            return

        output = filedialog.asksaveasfilename(
            title="儲存壓縮後的 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")]
        )
        if not output:
            return

        self._start_processing()
        quality = self.compress_var.get()
        orig_size = os.path.getsize(self.files[0])

        self._show_processing("正在壓縮 PDF...")

        def run():
            try:
                compress_pdf(self.files[0], output, quality)
                new_size = os.path.getsize(output)
                ratio = max(0, int((1 - new_size / orig_size) * 100))
                msg = f"壓縮完成！減少了 {ratio}% ({get_file_size_str(orig_size)} → {get_file_size_str(new_size)})"
                self.root.after(0, lambda: self._finish_success(msg, output))
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _do_watermark(self):
        if self.processing:
            return
        if not self.files:
            messagebox.showwarning("提示", "請先新增 PDF 檔案")
            return

        output = filedialog.asksaveasfilename(
            title="儲存帶浮水印的 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")]
        )
        if not output:
            return

        self._start_processing()
        opts = {
            "text": self.wm_text_var.get(),
            "font_size": self.wm_fontsize_var.get(),
            "color": self.wm_color_var.get(),
            "opacity": self.wm_opacity_var.get(),
            "rotation": self.wm_rotation_var.get(),
            "position": self.wm_position_var.get(),
        }

        self._show_processing("正在新增浮水印...")

        def run():
            try:
                add_watermark(self.files[0], output, **opts)
                self.root.after(0, lambda: self._finish_success("浮水印新增完成！", output))
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _do_toimage(self):
        if self.processing:
            return
        if not self.files:
            messagebox.showwarning("提示", "請先新增 PDF 檔案")
            return

        output_dir = filedialog.askdirectory(title="選擇圖片儲存目錄")
        if not output_dir:
            return

        self._start_processing()
        fmt = self.img_format_var.get()
        scale = self.img_scale_var.get()
        quality = self.img_quality_var.get()

        self._show_processing("正在轉換 PDF 為圖片...")

        def progress_cb(current, total):
            pct = int(current / total * 100)
            self.root.after(0, lambda: self._show_processing(
                f"正在轉換第 {current}/{total} 頁...", pct))

        def run():
            try:
                output_paths = pdf_to_images(
                    self.files[0], output_dir, format=fmt,
                    scale=scale, quality=quality,
                    progress_callback=progress_cb,
                )
                msg = f"成功轉換 {len(output_paths)} 頁為 {fmt.upper()} 圖片"
                self.root.after(0, lambda: self._finish_success(msg, output_paths[0] if output_paths else None))
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    # ── Word 轉 PDF ──────────────────────────────────────────────
    def _show_wordtopdf_options(self):
        """Word 轉 PDF 選項"""
        frame = tk.Frame(self.options_content, bg=COLOR_SURFACE)
        frame.pack(fill="x", pady=(8, 0))

        tk.Label(frame, text="選擇 Word 檔案",
                 font=(FONT_FAMILY, 10), bg=COLOR_SURFACE, fg=COLOR_TEXT).pack(anchor="w")

        # 顯示已選取的 Word 檔案
        self.wp_selected_path = tk.StringVar(value="")
        self.wp_selected_label = tk.Label(
            frame, text="尚未選擇檔案",
            font=(FONT_FAMILY, 10), bg="#f8fafc", fg="#94a3b8",
            anchor="w", padx=8, pady=6, relief="solid", bd=1
        )
        self.wp_selected_label.pack(fill="x", pady=(4, 8))

        def browse_word_file():
            path = filedialog.askopenfilename(
                title="選擇 Word 文件",
                filetypes=[
                    ("Word 文件", "*.docx;*.doc"),
                    ("所有檔案", "*.*")
                ]
            )
            if path and is_word_file(path):
                self.wp_selected_path.set(path)
                name = os.path.basename(path)
                size = get_file_size_str(os.path.getsize(path))
                self.wp_selected_label.config(
                    text=f"📄 {name}（{size}）",
                    fg=COLOR_TEXT, bg="#f0fdf4"
                )
            elif path:
                messagebox.showwarning("提示", "請選擇 .docx 或 .doc 檔案")

        browse_btn = tk.Button(frame, text="🗁 瀏覽選擇 Word 檔案",
                               font=(FONT_FAMILY, 10), bg=COLOR_PRIMARY, fg="white",
                               relief="flat", padx=16, pady=6, cursor="hand2",
                               activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                               command=browse_word_file)
        browse_btn.pack(pady=(0, 4))

        ttk.Label(frame, text="需要安裝 WPS Office 或 Microsoft Word 才能轉換",
                  style="BodyDim.TLabel").pack(anchor="w", pady=(0, 4))

        self._show_process_btn("轉換為 PDF", self._do_wordtopdf)

    def _do_wordtopdf(self):
        if self.processing:
            return

        input_path = self.wp_selected_path.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("提示", "請先選擇一個 Word 檔案")
            return

        output = filedialog.asksaveasfilename(
            title="儲存轉換後的 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")]
        )
        if not output:
            return

        self._start_processing()
        self._show_processing("正在轉換 Word 為 PDF（請稍候，Word 正在背景執行）...")

        def run():
            try:
                word_to_pdf(input_path, output)
                name = os.path.basename(output)
                self.root.after(0, lambda: self._finish_success(
                    f"✅ 轉換完成！已儲存為 {name}", output))
            except Exception as e:
                self.root.after(0, lambda: self._finish_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _start_processing(self):
        self.processing = True
        if hasattr(self, 'process_btn') and self.process_btn.winfo_exists():
            self.process_btn.config(state="disabled")

    def _finish_success(self, message: str, output_path: Optional[str] = None):
        self.processing = False
        if hasattr(self, 'process_btn') and self.process_btn.winfo_exists():
            self.process_btn.config(state="normal")
        self._show_success(message, output_path)

    def _finish_error(self, error: str):
        self.processing = False
        if hasattr(self, 'process_btn') and self.process_btn.winfo_exists():
            self.process_btn.config(state="normal")
        self._show_error(error)


# ── 启动 ───────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = PDFToolboxApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
