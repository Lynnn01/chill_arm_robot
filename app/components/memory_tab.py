"""
app/components/memory_tab.py — 2D Radar Spatial Map
"""
import tkinter as tk
from app.theme import Theme


class MemoryTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.SIDEBAR_BG)

        # Header
        hdr = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        hdr.pack(fill=tk.X, padx=Theme.SP_MD, pady=(Theme.SP_MD, Theme.SP_SM))
        tk.Label(hdr, text="2D Spatial Radar", font=Theme.FONT_H1,
                 bg=Theme.SIDEBAR_BG, fg=Theme.FG).pack(side=tk.LEFT)

        # Card
        card = tk.Frame(self, bg=Theme.SURFACE,
                        highlightbackground=Theme.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True,
                  padx=Theme.SP_MD, pady=(0, Theme.SP_MD))

        self.canvas = tk.Canvas(card, bg=Theme.SURFACE, bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", self._draw_radar)
        self._update_loop()

    def _get_color_from_name(self, name):
        name = name.lower()
        if "red" in name or "แดง" in name: return "#ff4444"
        if "blue" in name or "น้ำเงิน" in name or "ฟ้า" in name: return "#4444ff"
        if "green" in name or "เขียว" in name: return "#44ff44"
        if "yellow" in name or "เหลือง" in name: return "#ffff44"
        if "orange" in name or "ส้ม" in name: return "#ffa500"
        return "#ffffff"

    def _draw_radar(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        # Coordinate System: Base at bottom-center
        base_x = w / 2
        base_y = h - 30
        max_reach_mm = 280.0
        
        # Calculate scale to fit max reach
        scale_w = (w - 40) / (max_reach_mm * 2) # X spans -280 to 280
        scale_h = (h - 50) / max_reach_mm       # Y spans 0 to 280
        scale = min(scale_w, scale_h)
        if scale <= 0: scale = 0.5

        # Helper to map robot (x, y) to canvas (cx, cy)
        # Robot X is forward (up on canvas)
        # Robot Y is left (left on canvas)
        def r2c(rx, ry):
            cx = base_x - (ry * scale)
            cy = base_y - (rx * scale)
            return cx, cy

        # Draw Grid Rings
        radii = [100, 200, 280]
        for r in radii:
            cr = r * scale
            self.canvas.create_arc(
                base_x - cr, base_y - cr,
                base_x + cr, base_y + cr,
                start=0, extent=180,
                outline=Theme.BORDER, style=tk.ARC, dash=(2, 4)
            )
            # Label
            self.canvas.create_text(base_x + 5, base_y - cr + 5, text=f"{r}mm", fill=Theme.CAPTION_FG, font=("Inter", 7), anchor="nw")

        # Draw Robot Base
        br = 12
        self.canvas.create_oval(base_x - br, base_y - br, base_x + br, base_y + br, fill=Theme.SIDEBAR_BG, outline=Theme.BORDER, width=2)
        self.canvas.create_text(base_x, base_y + 15, text="BASE", fill=Theme.CAPTION_FG, font=Theme.FONT_CAPTION)

        try:
            import hardware.init as hw
            
            # Draw Known Objects
            for obj_name, coords in hw.known_objects.items():
                if not isinstance(coords, list) or len(coords) < 2:
                    continue
                rx, ry = coords[0], coords[1]
                cx, cy = r2c(rx, ry)
                color = self._get_color_from_name(obj_name)
                
                # Draw square for object
                s = 8
                self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s, fill=color, outline="#ffffff")
                self.canvas.create_text(cx, cy - 14, text=obj_name.split()[0], fill=Theme.FG, font=("Inter", 8))

            # Draw Current Arm Position (Crosshair)
            if hasattr(hw, 'last_coords') and hw.last_coords and len(hw.last_coords) >= 2:
                rx, ry = hw.last_coords[0], hw.last_coords[1]
                cx, cy = r2c(rx, ry)
                
                # Line from base to end effector
                self.canvas.create_line(base_x, base_y, cx, cy, fill=Theme.ACCENT, width=2, dash=(4, 4))
                
                # Crosshair
                cr = 10
                self.canvas.create_oval(cx - cr, cy - cr, cx + cr, cy + cr, outline=Theme.ACCENT, width=2)
                self.canvas.create_line(cx - cr - 4, cy, cx + cr + 4, cy, fill=Theme.ACCENT, width=2)
                self.canvas.create_line(cx, cy - cr - 4, cx, cy + cr + 4, fill=Theme.ACCENT, width=2)
                
                # Holding indicator
                if hw.is_holding_object:
                    obj = hw.current_held_object or "Object"
                    color = self._get_color_from_name(obj)
                    self.canvas.create_rectangle(cx - 6, cy - 6, cx + 6, cy + 6, fill=color, outline="#fff")
                    self.canvas.create_text(cx, cy - 18, text="Holding", fill=Theme.FG, font=("Inter", 8, "bold"))
                    
        except Exception as e:
            pass

    def _update_loop(self):
        self._draw_radar()
        self.after(500, self._update_loop)
