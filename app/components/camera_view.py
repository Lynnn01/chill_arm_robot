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
    W, H = 375, 375
    RADIUS = Theme.RADIUS_LG

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, bg=parent.cget("bg"), width=self.W, height=self.H, **kwargs)
        print(f"[DEBUG] CameraView Initialized! W={self.W}, H={self.H}")

        self._photo = None
        self.bind("<Configure>", self._draw_base)
        self._interval = 16  # default ~60fps, overridden by armconfig if loaded
        try:
            import armconfig
            self._interval = getattr(armconfig, 'GUI_CAMERA_INTERVAL_MS', 16)
        except Exception:
            pass
        self.after(self._interval, self._poll_frame)

    # ------------------------------------------------------------------
    def _draw_base(self, _event=None):
        self.delete("bg_card")
        w = self.winfo_width() or self.W
        h = self.winfo_height() or self.H
        self._rounded_rect(2, 2, w - 2, h - 2, self.RADIUS,
                            fill=Theme.SURFACE, outline=Theme.BORDER, tags="bg_card")
        self.tag_lower("bg_card")


    def _poll_frame(self):
        frame = None
        if _cam:
            try:
                frame = _cam.get_frame()
            except Exception:
                pass
        if frame is not None:
            import cv2
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Crop to square (center crop)
            fh, fw = frame_rgb.shape[:2]
            size = min(fh, fw)
            y1 = (fh - size) // 2
            x1 = (fw - size) // 2
            square_frame = frame_rgb[y1:y1+size, x1:x1+size]
            
            square_frame = cv2.resize(square_frame, (self.W - 20, self.H - 30))
            img = Image.fromarray(square_frame)
        else:
            img = Image.new("RGB", (self.W - 20, self.H - 30), Theme.SURFACE_MUTED)
        photo = ImageTk.PhotoImage(img)
        self._photo = photo
        self.delete("cam_img")
        w = self.winfo_width() or self.W
        # Center image slightly higher to leave room for text
        self.create_image(w // 2, (self.H - 14) // 2 - 5, image=photo, anchor="center", tags="cam_img")
        self.after(self._interval, self._poll_frame)

    # ------------------------------------------------------------------
    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
