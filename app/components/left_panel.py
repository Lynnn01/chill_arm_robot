import tkinter as tk
from tkinter import ttk
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
        
        self.grid(row=0, column=0, sticky="nsew", padx=(30,15), pady=30)
        self.columnconfigure(0, weight=1)

        # Title
        tk.Label(self, text="ONE ARM", font=("Tahoma", 28, "bold"), bg=self.theme["bg"], fg=self.theme["btn_bg"]).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Camera Feed
        self.cam_label = tk.Label(self, bg=self.theme["frame"], text="Camera Offline", fg=self.theme["fg"], font=("Tahoma", 14), width=60, height=20, relief=tk.FLAT)
        self.cam_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Modern Tabview using ttk.Notebook with custom styles
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.theme["bg"], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.theme["frame"], foreground=self.theme["fg"], font=("Tahoma", 12, "bold"), padding=[20, 10], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', self.theme["btn_bg"])], foreground=[('selected', self.theme["btn_fg"])])

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.rowconfigure(2, weight=1)

        # --- Tab 1: Control ---
        self.tab_control = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_control, text='Control')

        # Dashboard in Tab 1
        self.dash_frame = tk.Frame(self.tab_control, bg=self.theme["frame"])
        self.dash_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(self.dash_frame, text=" Live Robot Status ", font=("Tahoma", 14, "bold"), bg=self.theme["frame"], fg=self.theme["fg"]).grid(row=0, column=0, columnspan=6, pady=(15, 10))
        
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            lbl_title = tk.Label(self.dash_frame, text=f"{axis}:", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"])
            lbl_title.grid(row=(i//3)+1, column=(i%3)*2, sticky="e", padx=(25, 5), pady=15)
            
            lbl_val = tk.Label(self.dash_frame, text="---", font=("Tahoma", 12), bg=self.theme["dash_bg"], fg=self.theme["fg"], width=8, anchor="center")
            lbl_val.grid(row=(i//3)+1, column=(i%3)*2+1, sticky="w")
            self.status_labels[axis] = lbl_val

        # Quick Actions in Tab 1
        self.qa_frame = tk.Frame(self.tab_control, bg=self.theme["bg"])
        self.qa_frame.pack(fill=tk.X)
        
        def on_enter(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_hover"]
        def on_leave(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_bg"]

        btn_config = {"font":("Tahoma", 14, "bold"), "bg":self.theme["btn_bg"], "fg":self.theme["btn_fg"], "relief":tk.FLAT, "cursor":"hand2"}
        b1 = tk.Button(self.qa_frame, text="👋 โบกมือ", command=lambda: self.run_quick_action("โบกมือทักทายหน่อย"), **btn_config)
        b1.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True, ipady=10)
        
        b2 = tk.Button(self.qa_frame, text="👐 เปิดจับ", command=lambda: self.run_quick_action("เปิดหัวจับ"), **btn_config)
        b2.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True, ipady=10)
        
        b3 = tk.Button(self.qa_frame, text="✊ ปิดจับ", command=lambda: self.run_quick_action("ปิดหัวจับ"), **btn_config)
        b3.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True, ipady=10)
        
        b4 = tk.Button(self.qa_frame, text="🕺 เต้น", command=lambda: self.run_quick_action("เต้นให้ดูหน่อย"), **btn_config)
        b4.pack(side=tk.LEFT, padx=(5,0), fill=tk.X, expand=True, ipady=10)
        self.qa_btns.extend([b1, b2, b3, b4])
        
        for b in self.qa_btns:
            b.bind("<Enter>", on_enter)
            b.bind("<Leave>", on_leave)

        # --- Tab 2: Calibration ---
        self.tab_calib = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_calib, text='Calibration')

        calib_frame = tk.Frame(self.tab_calib, bg=self.theme["frame"])
        calib_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(calib_frame, text=" Camera to Robot Offsets ", font=("Tahoma", 14, "bold"), bg=self.theme["frame"], fg=self.theme["fg"]).grid(row=0, column=0, columnspan=2, pady=(15, 10))

        import json
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        self.calib_vars = {}
        for i, axis in enumerate(["x", "y", "z"]):
            lbl_title = tk.Label(calib_frame, text=f"Offset {axis.upper()}:", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"])
            lbl_title.grid(row=i+1, column=0, sticky="e", padx=(25, 5), pady=15)
            
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            ent = tk.Entry(calib_frame, textvariable=var, font=("Tahoma", 12), bg=self.theme["dash_bg"], fg=self.theme["fg"], width=15, insertbackground=self.theme["fg"], relief=tk.FLAT)
            ent.grid(row=i+1, column=1, sticky="w", pady=15)
            self.calib_vars[axis] = var
            
        btn_save = tk.Button(calib_frame, text="Save Calibration", font=("Tahoma", 12, "bold"), bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, cursor="hand2", command=self.save_calibration)
        btn_save.grid(row=4, column=0, columnspan=2, pady=20, ipadx=15, ipady=10)
        btn_save.bind("<Enter>", on_enter)
        btn_save.bind("<Leave>", on_leave)
        
        # --- Tab 3: Memory ---
        self.tab_memory = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_memory, text='Memory')
        
        self.memory_text = tk.Text(self.tab_memory, wrap=tk.WORD, bg=self.theme["dash_bg"], fg=self.theme["fg"], font=("Tahoma", 12), bd=0, relief=tk.FLAT, padx=15, pady=15)
        self.memory_text.pack(fill=tk.BOTH, expand=True, pady=20)
        self.memory_text.config(state=tk.DISABLED)

        self.update_camera_feed()
        self.start_dashboard_thread()
        self.update_memory_dashboard()

    def disable_buttons(self):
        for b in self.qa_btns:
            b.config(state=tk.DISABLED, bg="#555555")

    def enable_buttons(self):
        for b in self.qa_btns:
            b.config(state=tk.NORMAL, bg=self.theme["btn_bg"])

    def update_memory_dashboard(self):
        import hardware.init as hw_init
        self.memory_text.config(state=tk.NORMAL)
        self.memory_text.delete(1.0, tk.END)
        
        text_content = "🧠 Known Objects:\n\n"
        if not hw_init.known_objects:
            text_content += "   (Empty)\n"
        else:
            for obj, coords in hw_init.known_objects.items():
                if isinstance(coords, list):
                    text_content += f" 🔹 {obj}: [X: {coords[0]:.1f}, Y: {coords[1]:.1f}]\n"
                else:
                    text_content += f" 🔹 {obj}: {coords}\n"
                
        text_content += f"\n🖐️ Gripper Status:\n\n"
        if hw_init.is_holding_object:
            text_content += f" 🔸 Holding: {hw_init.current_held_object}\n"
        else:
            text_content += " 🔸 Empty\n"
            
        self.memory_text.insert(tk.END, text_content)
        self.memory_text.config(state=tk.DISABLED)
        
        self.after(1000, self.update_memory_dashboard)

    def save_calibration(self):
        import json
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {}
            
        for axis in ["x", "y", "z"]:
            config_data[axis] = self.calib_vars[axis].get()
            
        with open("config.json", "w") as f:
            json.dump(config_data, f, indent=4)
            
        def _notify():
            print("\n✅ <SYSTEM>: Calibration settings saved to config.json")
        self.log_queue.put(_notify)

    def update_camera_feed(self):
        frame = cam_manager.get_frame()
        if frame is not None and frame.size > 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (480, 360))
            
            pil_image = Image.fromarray(frame)
            if not hasattr(self, 'tk_image'):
                self.tk_image = ImageTk.PhotoImage(image=pil_image)
                self.cam_label.config(image=self.tk_image, text="")
            else:
                self.tk_image.paste(pil_image)
            
        self.after(50, self.update_camera_feed)

    def start_dashboard_thread(self):
        def _fetch_loop():
            import time
            while True:
                try:
                    coords = mc.get_coords()
                    if coords and len(coords) >= 6:
                        def _update_ui(c=coords):
                            for ax, val in zip(["X", "Y", "Z", "Rx", "Ry", "Rz"], c):
                                if ax in self.status_labels:
                                    self.status_labels[ax].config(text=f"{val:.1f}")
                        self.log_queue.put(_update_ui)
                except Exception:
                    pass
                time.sleep(0.5)
        threading.Thread(target=_fetch_loop, daemon=True).start()
