"""
app/components/calibration_tab.py — Camera-to-robot offset calibration panel
"""
import tkinter as tk
import json
from app.theme import Theme
from app.widgets import RoundedButton


class CalibrationTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.SIDEBAR_BG)
        self.calib_vars = {}

        # Header
        hdr = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        hdr.pack(fill=tk.X, padx=Theme.SP_MD, pady=(Theme.SP_MD, Theme.SP_SM))
        tk.Label(hdr, text="Camera → Robot Offsets", font=Theme.FONT_H1,
                 bg=Theme.SIDEBAR_BG, fg=Theme.FG).pack(side=tk.LEFT)

        # Card
        card = tk.Frame(self, bg=Theme.SURFACE,
                        highlightbackground=Theme.BORDER, highlightthickness=1)
        card.pack(fill=tk.X, padx=Theme.SP_MD, pady=(0, Theme.SP_MD))
        card_inner = tk.Frame(card, bg=Theme.SURFACE)
        card_inner.pack(fill=tk.X, padx=Theme.SP_MD, pady=Theme.SP_MD)

        # Load config
        try:
            from hardware.init import CONFIG_PATH
            with open(CONFIG_PATH, "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        for i, axis in enumerate(["x", "y", "z"]):
            row = tk.Frame(card_inner, bg=Theme.SURFACE)
            row.pack(fill=tk.X, pady=Theme.SP_SM)
            tk.Label(row, text=f"Offset {axis.upper()}", font=Theme.FONT_BODY_BOLD,
                     bg=Theme.SURFACE, fg=Theme.FG, width=12, anchor="w").pack(side=tk.LEFT)
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            entry = tk.Entry(row, textvariable=var, font=Theme.FONT_BODY,
                             bg=Theme.SURFACE_MUTED, fg=Theme.FG, width=12,
                             relief=tk.FLAT, bd=0, insertbackground=Theme.FG,
                             highlightbackground=Theme.BORDER, highlightthickness=1)
            entry.pack(side=tk.LEFT, ipady=6)
            self.calib_vars[axis] = var

        # Save button
        btn_frame = tk.Frame(card_inner, bg=Theme.SURFACE)
        btn_frame.pack(fill=tk.X, pady=(Theme.SP_MD, 0))

        save_btn = RoundedButton(btn_frame, text="Save Calibration",
                                 radius=Theme.RADIUS_SM,
                                 bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG,
                                 hover_bg=Theme.PRIMARY_HOVER,
                                 font=Theme.FONT_BODY_BOLD,
                                 command=self.save_calibration,
                                 height=40)
        save_btn.pack(fill=tk.X)

    def save_calibration(self):
        from hardware.init import CONFIG_PATH
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        for axis in ["x", "y", "z"]:
            data[axis] = self.calib_vars[axis].get()
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print("\n✅ <SYSTEM>: Calibration settings saved to config.json")
