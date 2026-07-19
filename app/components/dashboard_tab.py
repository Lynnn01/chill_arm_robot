import tkinter as tk
import threading
from app.theme import Theme

class DashboardTab(tk.Frame):
    def __init__(self, parent, log_queue):
        super().__init__(parent, bg=Theme.BG)
        self.log_queue = log_queue
        
        # Main container with 16px padding
        self.container = tk.Frame(self, bg=Theme.BG)
        self.container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        tk.Label(self.container, text="Live Robot Status", font=Theme.FONT_H2, bg=Theme.BG, fg=Theme.FG).pack(anchor="w", pady=(0, 16))
        
        # Bento Grid Frame
        self.bento_frame = tk.Frame(self.container, bg=Theme.BG)
        self.bento_frame.pack(fill=tk.X)
        self.bento_frame.columnconfigure(0, weight=1)
        self.bento_frame.columnconfigure(1, weight=1)
        self.bento_frame.columnconfigure(2, weight=1)
        
        self.status_labels = {}
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            # Individual Bento Card
            card = tk.Frame(self.bento_frame, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
            card.grid(row=i//3, column=i%3, sticky="nsew", padx=8, pady=8)
            card.columnconfigure(0, weight=1)
            
            tk.Label(card, text=f"{axis} Axis", font=Theme.FONT_SMALL, bg=Theme.SURFACE, fg=Theme.MUTED_FG).pack(anchor="center", pady=(16, 4))
            
            lbl_val = tk.Label(card, text="---", font=Theme.FONT_H2, bg=Theme.SURFACE, fg=Theme.FG)
            lbl_val.pack(anchor="center", pady=(0, 16))
            self.status_labels[axis] = lbl_val
            
        self._start_dashboard_loop()

    def _start_dashboard_loop(self):
        def _loop():
            import time
            import hardware.init as hw
            while True:
                try:
                    coords = hw.mc.get_coords()
                    if coords and len(coords) >= 6:
                        hw.last_coords = coords
                        def _update(c=coords):
                            for ax, val in zip(["X", "Y", "Z", "Rx", "Ry", "Rz"], c):
                                if ax in self.status_labels:
                                    self.status_labels[ax].config(text=f"{val:.1f}")
                        self.log_queue.put(_update)
                except Exception:
                    pass
                time.sleep(0.5)
        threading.Thread(target=_loop, daemon=True).start()
