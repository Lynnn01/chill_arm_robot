import tkinter as tk
from tkinter import ttk
from app.theme import Theme
from app.components.camera_view import CameraView
from app.components.dashboard_tab import DashboardTab
from app.components.calibration_tab import CalibrationTab
from app.components.memory_tab import MemoryTab

class LeftPanel(tk.Frame):
    def __init__(self, parent, log_queue):
        super().__init__(parent, bg=Theme.BG)
        self.log_queue = log_queue
        
        self.grid(row=0, column=0, sticky="nsew", padx=(30,15), pady=30)
        self.columnconfigure(0, weight=1)

        # Title
        tk.Label(self, text="ONE ARM", font=Theme.FONT_TITLE, bg=Theme.BG, fg=Theme.PRIMARY).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Camera Feed Component
        self.camera_view = CameraView(self)
        self.camera_view.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=Theme.BG, borderwidth=0)
        style.configure('TNotebook.Tab', background=Theme.SURFACE_MUTED, foreground=Theme.MUTED_FG, font=Theme.FONT_BODY_BOLD, padding=[20, 10], borderwidth=1, relief="solid")
        style.map('TNotebook.Tab', background=[('selected', Theme.SURFACE)], foreground=[('selected', Theme.FG)])

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.rowconfigure(2, weight=1)

        # Control Tab
        self.dashboard_tab = DashboardTab(self.notebook, log_queue=self.log_queue)
        self.notebook.add(self.dashboard_tab, text='Control')

        # Calibration Tab
        self.calibration_tab = CalibrationTab(self.notebook)
        self.notebook.add(self.calibration_tab, text='Calibration')
        
        # Memory Tab
        self.memory_tab = MemoryTab(self.notebook)
        self.notebook.add(self.memory_tab, text='Memory')

    def disable_buttons(self):
        # Quick action buttons were removed, but this method might be called by gui.py
        pass

    def enable_buttons(self):
        # Quick action buttons were removed, but this method might be called by gui.py
        pass
