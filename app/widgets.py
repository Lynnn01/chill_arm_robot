"""
app/widgets.py — Custom rounded widgets for tkinter
Implements rounded-corner UI elements that standard tkinter doesn't support natively.
"""
import tkinter as tk
from app.theme import Theme


class RoundedFrame(tk.Canvas):
    """
    A canvas-backed widget that draws a rounded-corner rectangle as its background.
    Children are placed inside an inner tk.Frame embedded in the canvas.
    """

    def __init__(self, parent, radius=16, bg=None, border_color=None, **kwargs):
        self._radius = radius
        self._bg = bg or Theme.SURFACE
        self._border_color = border_color or Theme.BORDER
        
        # Canvas itself uses parent bg so it blends in
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, bg=parent.cget("bg") if hasattr(parent, "cget") else Theme.BG, **kwargs)
        
        # Inner frame where children are packed
        self.inner = tk.Frame(self, bg=self._bg)
        
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        r = min(self._radius, w // 2, h // 2)
        
        if w < 4 or h < 4:
            return
            
        # Draw filled rounded rect
        self._draw_rounded_rect(2, 2, w - 2, h - 2, r, fill=self._bg, outline=self._border_color, tag="bg")
        
        # Place inner frame inside, make it smaller so it doesn't cover the outline
        self.create_window(w // 2, h // 2, window=self.inner, anchor="center", 
                           width=max(1, w - 8), height=max(1, h - 8), tags="bg")
        self.tag_lower("bg")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        tag = kwargs.pop("tag", None)
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        if tag:
            return self.create_polygon(points, smooth=True, tags=tag, **kwargs)
        return self.create_polygon(points, smooth=True, **kwargs)

    def configure_colors(self, bg=None, border_color=None):
        if bg:
            self._bg = bg
            self.inner.configure(bg=bg)
        if border_color:
            self._border_color = border_color
        self._redraw()


class RoundedButton(tk.Canvas):
    """
    A canvas-backed rounded button with hover and disabled states.
    """

    def __init__(self, parent, text="", radius=10, 
                 bg=None, fg=None, hover_bg=None,
                 font=None, command=None, **kwargs):
        self._text = text
        self._radius = radius
        self._bg_normal = bg or Theme.PRIMARY
        self._bg_hover = hover_bg or Theme.PRIMARY_HOVER
        self._bg_current = self._bg_normal
        self._fg = fg or Theme.PRIMARY_FG
        self._font = font or Theme.FONT_BODY_BOLD
        self._command = command
        self._disabled = False

        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("cursor", "hand2")
        super().__init__(parent, bg=parent.cget("bg") if hasattr(parent, "cget") else Theme.BG, **kwargs)

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        r = min(self._radius, w // 2, h // 2)
        
        color = Theme.MUTED_FG if self._disabled else self._bg_current
        self._draw_rounded_rect(0, 0, w, h, r, fill=color, outline=color)
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg,
                         font=self._font, anchor="center")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1,
        ]
        self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, e):
        if not self._disabled:
            self._bg_current = self._bg_hover
            self._redraw()

    def _on_leave(self, e):
        if not self._disabled:
            self._bg_current = self._bg_normal
            self._redraw()

    def _on_click(self, e):
        if not self._disabled and self._command:
            self._command()

    def set_text(self, text):
        self._text = text
        self._redraw()

    def set_state(self, state):
        self._disabled = (state == tk.DISABLED)
        self.configure(cursor="arrow" if self._disabled else "hand2")
        self._redraw()

    def set_colors(self, bg=None, fg=None, hover_bg=None):
        if bg:
            self._bg_normal = bg
            self._bg_hover = hover_bg or bg
            if not self._disabled:
                self._bg_current = bg
        elif hover_bg:
            self._bg_hover = hover_bg
        if fg:
            self._fg = fg
        self._redraw()
