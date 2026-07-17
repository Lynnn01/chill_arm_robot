import tkinter as tk
import customtkinter as ctk
import threading
import cv2
from PIL import Image
from hardware.init import cam_manager, mc

class LeftPanel(ctk.CTkFrame):
    def __init__(self, parent, log_queue, run_quick_action_callback):
        super().__init__(parent, fg_color="transparent")
        self.log_queue = log_queue
        self.run_quick_action = run_quick_action_callback
        self.qa_btns = []
        self.status_labels = {}
        
        self.grid(row=0, column=0, sticky="nsew", padx=(30,10), pady=30)
        self.columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(self, text="ONE ARM", font=("Tahoma", 28, "bold"), text_color="#3B8ED0")
        title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Camera Feed
        self.cam_label = ctk.CTkLabel(self, text="Camera Offline", font=("Tahoma", 14), fg_color="#1E1E1E", corner_radius=15)
        self.cam_label.grid(row=1, column=0, sticky="ew", pady=(0, 20), ipady=180)
        
        # Modern Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)

        self.tabview.add("Control")
        self.tabview.add("Calibration")
        self.tabview.add("Memory")

        # --- Tab 1: Control ---
        control_tab = self.tabview.tab("Control")
        
        # Dashboard Frame
        self.dash_frame = ctk.CTkFrame(control_tab, corner_radius=10, fg_color="#2A2A2A")
        self.dash_frame.pack(fill=tk.X, pady=(10, 20), padx=10, ipadx=10, ipady=10)
        
        ctk.CTkLabel(self.dash_frame, text="Live Robot Status", font=("Tahoma", 14, "bold")).grid(row=0, column=0, columnspan=6, pady=(0, 10))
        
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            lbl_title = ctk.CTkLabel(self.dash_frame, text=f"{axis}:", font=("Tahoma", 12, "bold"))
            lbl_title.grid(row=(i//3)+1, column=(i%3)*2, sticky="e", padx=(15, 5), pady=10)
            
            lbl_val = ctk.CTkLabel(self.dash_frame, text="---", font=("Tahoma", 12), width=60, fg_color="#1E1E1E", corner_radius=5)
            lbl_val.grid(row=(i//3)+1, column=(i%3)*2+1, sticky="w")
            self.status_labels[axis] = lbl_val

        # Quick Actions Frame
        self.qa_frame = ctk.CTkFrame(control_tab, fg_color="transparent")
        self.qa_frame.pack(fill=tk.X, padx=10)
        
        btn_config = {"font":("Tahoma", 14, "bold"), "corner_radius":10, "height":40}
        b1 = ctk.CTkButton(self.qa_frame, text="👋 โบกมือ", command=lambda: self.run_quick_action("โบกมือทักทายหน่อย"), **btn_config)
        b1.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        
        b2 = ctk.CTkButton(self.qa_frame, text="👐 เปิดจับ", command=lambda: self.run_quick_action("เปิดหัวจับ"), **btn_config)
        b2.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        b3 = ctk.CTkButton(self.qa_frame, text="✊ ปิดจับ", command=lambda: self.run_quick_action("ปิดหัวจับ"), **btn_config)
        b3.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        b4 = ctk.CTkButton(self.qa_frame, text="🕺 เต้น", command=lambda: self.run_quick_action("เต้นให้ดูหน่อย"), **btn_config)
        b4.pack(side=tk.LEFT, padx=(5,0), fill=tk.X, expand=True)
        self.qa_btns.extend([b1, b2, b3, b4])

        # --- Tab 2: Calibration ---
        calib_tab = self.tabview.tab("Calibration")
        calib_frame = ctk.CTkFrame(calib_tab, corner_radius=10, fg_color="#2A2A2A")
        calib_frame.pack(fill=tk.X, pady=(10, 20), padx=10, ipadx=10, ipady=10)
        
        ctk.CTkLabel(calib_frame, text="Camera to Robot Offsets", font=("Tahoma", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        import json
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        self.calib_vars = {}
        for i, axis in enumerate(["x", "y", "z"]):
            ctk.CTkLabel(calib_frame, text=f"Offset {axis.upper()}:", font=("Tahoma", 12, "bold")).grid(row=i+1, column=0, sticky="e", padx=(15, 5), pady=10)
            
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            ent = ctk.CTkEntry(calib_frame, textvariable=var, font=("Tahoma", 12), width=100, justify="center")
            ent.grid(row=i+1, column=1, sticky="w", pady=10)
            self.calib_vars[axis] = var
            
        ctk.CTkButton(calib_frame, text="Save Calibration", font=("Tahoma", 12, "bold"), corner_radius=10, command=self.save_calibration).grid(row=4, column=0, columnspan=2, pady=15)
        
        # --- Tab 3: Memory ---
        mem_tab = self.tabview.tab("Memory")
        
        self.memory_text = ctk.CTkTextbox(mem_tab, wrap=tk.WORD, font=("Tahoma", 12), corner_radius=10, fg_color="#2A2A2A")
        self.memory_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.memory_text.configure(state=tk.DISABLED)

        self.update_camera_feed()
        self.start_dashboard_thread()
        self.update_memory_dashboard()

    def update_memory_dashboard(self):
        import hardware.init as hw_init
        self.memory_text.configure(state=tk.NORMAL)
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
        self.memory_text.configure(state=tk.DISABLED)
        
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
            
            if not hasattr(self, 'ctk_image'):
                self.ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(480, 360))
                self.cam_label.configure(image=self.ctk_image, text="")
            else:
                self.ctk_image.configure(light_image=pil_image, dark_image=pil_image)
                
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
                                    self.status_labels[ax].configure(text=f"{val:.1f}")
                        self.log_queue.put(_update_ui)
                except Exception:
                    pass
                time.sleep(0.5)
        threading.Thread(target=_fetch_loop, daemon=True).start()
