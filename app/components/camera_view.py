"""
app/components/camera_view.py — Camera feed with rounded card wrapper
"""
import tkinter as tk
from PIL import Image, ImageTk
from app.theme import Theme

try:
    from hardware.init import cam_manager as _cam
except Exception:
    _cam = None


class CameraView(tk.Canvas):
    """
    Rounded camera card. Draws a rounded rect background then composites the
    camera frame on top as a canvas image — so the rounded corners are visible.
    """
    W, H = 480, 360
    RADIUS = Theme.RADIUS_LG

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, bg=parent.cget("bg"), width=self.W, height=self.H + 40, **kwargs)

        self._photo = None
        self.bind("<Configure>", self._draw_base)
        self.after(50, self._poll_frame)

    # ------------------------------------------------------------------
    def _draw_base(self, _event=None):
        self.delete("bg_card")
        w = self.winfo_width() or (self.W + 4)
        h = self.winfo_height() or (self.H + 40)
        self._rounded_rect(2, 2, w - 2, h - 2, self.RADIUS,
                            fill=Theme.SURFACE, outline=Theme.BORDER, tags="bg_card")
        self.tag_lower("bg_card")
        # label
        self.delete("cam_label")
        self.create_text(w // 2, h - 14, text="Camera Feed",
                         font=Theme.FONT_CAPTION, fill=Theme.CAPTION_FG, tags="cam_label")

    def _poll_frame(self):
        frame = None
        if _cam:
            try:
                frame = _cam.get_frame()
            except Exception:
                pass
        if frame is not None:
            img = Image.fromarray(frame).resize((self.W, self.H))
        else:
            img = Image.new("RGB", (self.W, self.H), "#E2E8F0")
        photo = ImageTk.PhotoImage(img)
        self._photo = photo
        self.delete("cam_img")
        w = self.winfo_width() or (self.W + 4)
        self.create_image(w // 2, 8 + self.H // 2, image=photo, anchor="center", tags="cam_img")
        self.after(50, self._poll_frame)

    # ------------------------------------------------------------------
    @staticmethod
    def _rounded_rect(canvas_or_self, x1=None, y1=None, x2=None, y2=None, r=None, **kwargs):
        # Support both call styles
        if isinstance(canvas_or_self, CameraView):
            c = canvas_or_self
        else:
            c = canvas_or_self
        points = [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1,
        ]
        return c.create_polygon(points, smooth=True, **kwargs)


# Patch instance method
def _cv_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return self.create_polygon(points, smooth=True, **kwargs)


CameraView._rounded_rect = _cv_rounded_rect
