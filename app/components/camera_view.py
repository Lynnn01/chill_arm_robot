import tkinter as tk
import threading
import cv2
from PIL import Image, ImageTk
from hardware.init import cam_manager
from app.theme import Theme

class CameraView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.BG)
        
        self.card = tk.Frame(self, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1, width=320, height=240)
        self.card.pack_propagate(False)
        self.card.pack(fill=tk.NONE, pady=10)

        self.cam_label = tk.Label(
            self.card, bg=Theme.SURFACE, text="Camera Offline", fg=Theme.MUTED_FG,
            font=Theme.FONT_H2, relief=tk.FLAT
        )
        self.cam_label.pack(fill=tk.BOTH, expand=True)
        
        self._pending_image = None
        self._start_camera_processor()

    def _start_camera_processor(self):
        def _process_loop():
            while True:
                try:
                    raw = cam_manager.get_frame()
                    if raw is not None and raw.size > 0:
                        rgb = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
                        resized = cv2.resize(rgb, (320, 240))
                        self._pending_image = Image.fromarray(resized)
                except Exception:
                    pass
                import time
                time.sleep(0.05)
        threading.Thread(target=_process_loop, daemon=True).start()
        self._apply_camera_frame()

    def _apply_camera_frame(self):
        img = self._pending_image
        if img is not None:
            self._pending_image = None
            if not hasattr(self, 'tk_image'):
                self.tk_image = ImageTk.PhotoImage(image=img)
                self.cam_label.config(image=self.tk_image, text="")
            else:
                self.tk_image.paste(img)
        self.after(50, self._apply_camera_frame)
