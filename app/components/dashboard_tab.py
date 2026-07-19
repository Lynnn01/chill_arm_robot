"""
app/components/dashboard_tab.py — Bento Grid robot status cards
"""
import tkinter as tk
import threading
from app.theme import Theme
from app.widgets import RoundedFrame


class DashboardTab(tk.Frame):
    AXES = ["X", "Y", "Z", "Rx", "Ry", "Rz"]

    def __init__(self, parent, log_queue):
        super().__init__(parent, bg=Theme.SIDEBAR_BG)
        self.log_queue = log_queue
        self.status_labels = {}

        # Section header
        hdr = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        hdr.pack(fill=tk.X, padx=Theme.SP_MD, pady=(Theme.SP_MD, Theme.SP_SM))
        tk.Label(hdr, text="Live Robot Status", font=Theme.FONT_H1,
                 bg=Theme.SIDEBAR_BG, fg=Theme.FG).pack(side=tk.LEFT)

        # Bento grid — 3 columns
        grid = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        grid.pack(fill=tk.X, padx=Theme.SP_SM)
        for col in range(3):
            grid.columnconfigure(col, weight=1)

        for i, axis in enumerate(self.AXES):
            card = self._make_bento_card(grid, axis)
            card.grid(row=i // 3, column=i % 3,
                      padx=Theme.SP_SM, pady=Theme.SP_SM, sticky="nsew")

        self._start_poll()

    # ------------------------------------------------------------------
    def _make_bento_card(self, parent, axis):
        outer = tk.Frame(parent, bg=Theme.SURFACE,
                         highlightbackground=Theme.BORDER, highlightthickness=1)
        inner = tk.Frame(outer, bg=Theme.SURFACE)
        inner.pack(padx=Theme.SP_MD, pady=Theme.SP_MD)

        tk.Label(inner, text=f"{axis} Axis", font=Theme.FONT_CAPTION,
                 bg=Theme.SURFACE, fg=Theme.CAPTION_FG).pack()
        val = tk.Label(inner, text="---", font=Theme.FONT_H1,
                       bg=Theme.SURFACE, fg=Theme.FG, width=7)
        val.pack(pady=(Theme.SP_XS, 0))
        self.status_labels[axis] = val
        return outer

    def _start_poll(self):
        def _loop():
            import time
            try:
                import hardware.init as hw
            except Exception:
                return
            while True:
                try:
                    coords = hw.mc.get_coords()
                    if coords and len(coords) >= 6:
                        hw.last_coords = coords
                        def _update(c=coords):
                            for ax, val in zip(self.AXES, c):
                                if ax in self.status_labels:
                                    self.status_labels[ax].config(text=f"{val:.1f}")
                        self.log_queue.put(_update)
                except Exception:
                    pass
                time.sleep(0.5)
        threading.Thread(target=_loop, daemon=True).start()
