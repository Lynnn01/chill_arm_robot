"""
app/components/left_panel.py — Sidebar: brand, camera, and tabbed controls
"""
import tkinter as tk
from tkinter import ttk
from app.theme import Theme
from app.components.camera_view import CameraView
from app.components.dashboard_tab import DashboardTab
from app.components.calibration_tab import CalibrationTab
from app.components.memory_tab import MemoryTab


class LeftPanel(tk.Frame):
    def __init__(self, parent, log_queue):
        super().__init__(parent, bg=Theme.SIDEBAR_BG)
        self.log_queue = log_queue

        # Right separator
        sep = tk.Frame(self, bg=Theme.BORDER, width=1)
        sep.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")

        self.grid(row=0, column=0, sticky="nsew",
                  padx=(Theme.SP_XL, 0), pady=Theme.SP_XL)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Brand ──────────────────────────────────────────────────────
        brand = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        brand.grid(row=0, column=0, sticky="ew",
                   padx=Theme.SP_MD, pady=(Theme.SP_MD, 0))
        tk.Label(brand, text="ONE ARM",
                 font=Theme.FONT_BRAND, bg=Theme.SIDEBAR_BG, fg=Theme.FG).pack(side=tk.LEFT)
        tk.Label(brand, text="AI Control",
                 font=Theme.FONT_SMALL, bg=Theme.SIDEBAR_BG, fg=Theme.CAPTION_FG).pack(side=tk.LEFT, padx=(Theme.SP_SM, 0), pady=(4, 0))

        # thin divider
        tk.Frame(self, height=1, bg=Theme.BORDER).grid(
            row=1, column=0, sticky="ew", padx=Theme.SP_MD, pady=Theme.SP_SM)

        # ── Camera ─────────────────────────────────────────────────────
        cam_wrapper = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        cam_wrapper.grid(row=2, column=0, sticky="ew", padx=Theme.SP_MD, pady=(0, Theme.SP_SM))
        cam_wrapper.columnconfigure(0, weight=1)
        self.camera_view = CameraView(cam_wrapper)
        self.camera_view.pack(fill=tk.X)

        # ── Notebook ───────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")  # Clam theme removes the ugly dotted focus ring
        style.configure("Sleek.TNotebook",
                        background=Theme.SIDEBAR_BG, borderwidth=0, relief="flat",
                        lightcolor=Theme.SIDEBAR_BG, darkcolor=Theme.SIDEBAR_BG, bordercolor=Theme.SIDEBAR_BG)
        style.configure("Sleek.TNotebook.Tab",
                        background=Theme.SURFACE_MUTED,
                        foreground=Theme.CAPTION_FG,
                        font=Theme.FONT_BODY_BOLD,
                        padding=[16, 6],
                        borderwidth=0,
                        focuscolor=Theme.SIDEBAR_BG)
        style.map("Sleek.TNotebook.Tab",
                  background=[("selected", Theme.SIDEBAR_BG)],
                  foreground=[("selected", Theme.FG)],
                  padding=[("selected", [16, 10])],
                  expand=[("selected", [0, 0, 0, 0])])

        self.notebook = ttk.Notebook(self, style="Sleek.TNotebook")
        self.notebook.grid(row=3, column=0, sticky="nsew",
                           padx=Theme.SP_MD, pady=(0, Theme.SP_MD))
        self.rowconfigure(3, weight=1)

        self.dashboard_tab = DashboardTab(self.notebook, log_queue=self.log_queue)
        self.notebook.add(self.dashboard_tab, text=" Control ")

        self.calibration_tab = CalibrationTab(self.notebook)
        self.notebook.add(self.calibration_tab, text=" Calibration ")

        self.memory_tab = MemoryTab(self.notebook)
        self.notebook.add(self.memory_tab, text=" Memory ")

    # kept for api compatibility
    def disable_buttons(self): pass
    def enable_buttons(self): pass
