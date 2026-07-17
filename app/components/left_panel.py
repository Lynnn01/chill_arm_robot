import tkinter as tk
import threading
import cv2
from PIL import Image, ImageTk
from hardware.init import cam_manager, mc

class LeftPanel(tk.Frame):
    def __init__(self, parent, theme, log_queue, run_quick_action_callback):
        super().__init__(parent, bg=theme["bg"])
        self.theme = theme
        self.log_queue = log_queue
        self.run_quick_action = run_quick_action_callback
        self.qa_btns = []
        self.status_labels = {}
        
        self.grid(row=0, column=0, sticky="nsew", padx=(30,10), pady=30)
        self.columnconfigure(0, weight=1)

        # Title
        tk.Label(self, text="ONE ARM", font=("Tahoma", 28, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Camera Feed
        self.cam_label = tk.Label(self, bg="#000000", text="Camera Offline", fg="white", font=("Tahoma", 12))
        self.cam_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Dashboard
        self.dash_frame = tk.LabelFrame(self, text=" Live Robot Status ", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"], bd=2, relief=tk.FLAT, highlightbackground=self.theme["border"], highlightthickness=1)
        self.dash_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20), ipadx=10, ipady=10)
        
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            lbl_title = tk.Label(self.dash_frame, text=f"{axis}:", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"])
            lbl_title.grid(row=i//3, column=(i%3)*2, sticky="e", padx=(15, 5), pady=10)
            
            lbl_val = tk.Label(self.dash_frame, text="---", font=("Tahoma", 12), bg=self.theme["dash_bg"], fg=self.theme["fg"], width=6, anchor="center")
            lbl_val.grid(row=i//3, column=(i%3)*2+1, sticky="w")
            self.status_labels[axis] = lbl_val

        # Quick Actions
        self.qa_frame = tk.Frame(self, bg=self.theme["bg"])
        self.qa_frame.grid(row=3, column=0, sticky="ew")
        
        btn_config = {"font":("Tahoma", 11, "bold"), "bg":self.theme["btn_bg"], "fg":self.theme["btn_fg"], "relief":tk.FLAT, "cursor":"hand2"}
        b1 = tk.Button(self.qa_frame, text="👋 โบกมือ", command=lambda: self.run_quick_action("โบกมือทักทายหน่อย"), **btn_config)
        b1.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True, ipady=5)
        
        b2 = tk.Button(self.qa_frame, text="👐 เปิดจับ", command=lambda: self.run_quick_action("เปิดหัวจับ"), **btn_config)
        b2.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True, ipady=5)
        
        b3 = tk.Button(self.qa_frame, text="✊ ปิดจับ", command=lambda: self.run_quick_action("ปิดหัวจับ"), **btn_config)
        b3.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True, ipady=5)
        
        b4 = tk.Button(self.qa_frame, text="🕺 เต้น", command=lambda: self.run_quick_action("เต้นให้ดูหน่อย"), **btn_config)
        b4.pack(side=tk.LEFT, padx=(5,0), fill=tk.X, expand=True, ipady=5)
        self.qa_btns.extend([b1, b2, b3, b4])

        self.update_camera_feed()
        self.update_dashboard()

    def update_camera_feed(self):
        frame = cam_manager.get_frame()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (480, 360))
            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.cam_label.config(image=img, text="")
            self.cam_label.image = img
        self.after(50, self.update_camera_feed)

    def update_dashboard(self):
        def _fetch():
            try:
                coords = mc.get_coords()
                if coords and len(coords) >= 6:
                    def _update_ui():
                        for ax, val in zip(["X", "Y", "Z", "Rx", "Ry", "Rz"], coords):
                            self.status_labels[ax].config(text=f"{val:.1f}")
                    self.log_queue.put(_update_ui)
            except:
                pass
            self.after(500, self.update_dashboard)
        threading.Thread(target=_fetch, daemon=True).start()
