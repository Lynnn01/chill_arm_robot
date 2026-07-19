import tkinter as tk
import json
from app.theme import Theme

class CalibrationTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.BG)
        
        self.card = tk.Frame(self, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
        self.card.pack(fill=tk.X, pady=10)
        
        tk.Label(self.card, text="Camera to Robot Offsets", font=Theme.FONT_H2, bg=Theme.SURFACE, fg=Theme.FG).grid(row=0, column=0, columnspan=2, pady=(15, 10))
        
        try:
            from hardware.init import CONFIG_PATH
            with open(CONFIG_PATH, "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        self.calib_vars = {}
        for i, axis in enumerate(["x", "y", "z"]):
            tk.Label(self.card, text=f"Offset {axis.upper()}:", font=Theme.FONT_BODY_BOLD, bg=Theme.SURFACE, fg=Theme.FG).grid(row=i+1, column=0, sticky="e", padx=(25, 5), pady=15)
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            tk.Entry(self.card, textvariable=var, font=Theme.FONT_BODY, bg=Theme.SURFACE_MUTED, fg=Theme.FG, width=15, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1, insertbackground=Theme.FG).grid(row=i+1, column=1, sticky="w", pady=15)
            self.calib_vars[axis] = var
            
        btn_save = tk.Button(self.card, text="Save Calibration", font=Theme.FONT_BODY_BOLD, bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG, relief=tk.FLAT, cursor="hand2", command=self.save_calibration)
        btn_save.grid(row=4, column=0, columnspan=2, pady=20, ipadx=15, ipady=10)
        btn_save.bind("<Enter>", lambda e: e.widget.config(background=Theme.PRIMARY_HOVER) if e.widget['state'] != tk.DISABLED else None)
        btn_save.bind("<Leave>", lambda e: e.widget.config(background=Theme.PRIMARY) if e.widget['state'] != tk.DISABLED else None)

    def save_calibration(self):
        from hardware.init import CONFIG_PATH
        import json
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
