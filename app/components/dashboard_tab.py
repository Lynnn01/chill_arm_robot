import tkinter as tk
import threading
from app.theme import Theme

class DashboardTab(tk.Frame):
    def __init__(self, parent, log_queue):
        super().__init__(parent, bg=Theme.BG)
        self.log_queue = log_queue
        
        # Wrap in a card-like frame
        self.card = tk.Frame(self, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
        self.card.pack(fill=tk.X, pady=10)
        
        tk.Label(self.card, text="Live Robot Status", font=Theme.FONT_H2, bg=Theme.SURFACE, fg=Theme.FG).grid(row=0, column=0, columnspan=6, pady=(15, 10))
        
        self.status_labels = {}
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            tk.Label(self.card, text=f"{axis}:", font=Theme.FONT_BODY_BOLD, bg=Theme.SURFACE, fg=Theme.FG).grid(row=(i//3)+1, column=(i%3)*2, sticky="e", padx=(20, 5), pady=15)
            lbl_val = tk.Label(self.card, text="---", font=Theme.FONT_BODY, bg=Theme.SURFACE_MUTED, fg=Theme.FG, width=8, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
            lbl_val.grid(row=(i//3)+1, column=(i%3)*2+1, sticky="w")
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
