import tkinter as tk
import threading
import cv2
from PIL import Image, ImageTk
from hardware.init import cam_manager, mc
import hardware.init as hw_init

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
        
        from tkinter import ttk
        import json
        
        # Notebook for bottom half
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.theme["bg"], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.theme["frame"], foreground=self.theme["fg"], font=("Tahoma", 10, "bold"), padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', self.theme["dash_bg"])])

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.rowconfigure(2, weight=1)

        # Tab 1: Control
        self.tab_control = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_control, text='Control')

        # Dashboard in Tab 1
        self.dash_frame = tk.LabelFrame(self.tab_control, text=" Live Robot Status ", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"], bd=2, relief=tk.FLAT, highlightbackground=self.theme["border"], highlightthickness=1)
        self.dash_frame.pack(fill=tk.X, pady=(10, 20), ipadx=10, ipady=10)
        
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            lbl_title = tk.Label(self.dash_frame, text=f"{axis}:", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"])
            lbl_title.grid(row=i//3, column=(i%3)*2, sticky="e", padx=(15, 5), pady=10)
            
            lbl_val = tk.Label(self.dash_frame, text="---", font=("Tahoma", 12), bg=self.theme["dash_bg"], fg=self.theme["fg"], width=6, anchor="center")
            lbl_val.grid(row=i//3, column=(i%3)*2+1, sticky="w")
            self.status_labels[axis] = lbl_val

        # Quick Actions in Tab 1
        self.qa_frame = tk.Frame(self.tab_control, bg=self.theme["bg"])
        self.qa_frame.pack(fill=tk.X)
        
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

        # Tab 2: Calibration
        self.tab_calib = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_calib, text='Calibration')

        calib_frame = tk.LabelFrame(self.tab_calib, text=" Camera to Robot Offsets ", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"], bd=2, relief=tk.FLAT, highlightbackground=self.theme["border"], highlightthickness=1)
        calib_frame.pack(fill=tk.X, pady=(10, 20), ipadx=10, ipady=10)

        # Load current config
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        self.calib_vars = {}
        for i, axis in enumerate(["x", "y", "z"]):
            lbl_title = tk.Label(calib_frame, text=f"Offset {axis.upper()}:", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"])
            lbl_title.grid(row=i, column=0, sticky="e", padx=(15, 5), pady=10)
            
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            ent = tk.Entry(calib_frame, textvariable=var, font=("Tahoma", 12), bg=self.theme["dash_bg"], fg=self.theme["fg"], width=10, insertbackground=self.theme["fg"])
            ent.grid(row=i, column=1, sticky="w")
            self.calib_vars[axis] = var

        save_btn = tk.Button(calib_frame, text="💾 Save Calibration", command=self.save_calibration, font=("Tahoma", 11, "bold"), bg="#4CAF50", fg="white", relief=tk.FLAT, cursor="hand2")
        save_btn.grid(row=3, column=0, columnspan=2, pady=15, ipadx=20, ipady=5)

        # Tab 3: Memory
        self.tab_memory = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_memory, text='Memory')
        
        mem_frame = tk.LabelFrame(self.tab_memory, text=" AI Object Memory ", font=("Tahoma", 12, "bold"), bg=self.theme["frame"], fg=self.theme["fg"], bd=2, relief=tk.FLAT, highlightbackground=self.theme["border"], highlightthickness=1)
        mem_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 20), ipadx=10, ipady=10)
        
        self.memory_text = tk.Text(mem_frame, wrap=tk.WORD, bg=self.theme["dash_bg"], fg=self.theme["fg"], font=("Tahoma", 11), bd=0, relief=tk.FLAT)
        self.memory_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.memory_text.config(state=tk.DISABLED)

        self.update_camera_feed()
        self.update_dashboard()
        self.update_memory_dashboard()

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
        if frame is not None:
            # Resize
            frame = cv2.resize(frame, (640, 480))
            
            # Draw Crosshair
            cx, cy = 320, 240
            cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 0), 1)
            cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 0), 1)
            cv2.circle(frame, (cx, cy), 15, (0, 255, 0), 1)
            
            # Draw HUD Background overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 430), (640, 480), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            # HUD Text
            holding_status = "Holding Object" if hw_init.is_holding_object else "Empty"
            memory_count = f"Memory: {len(hw_init.known_objects)} items"
            cv2.putText(frame, f"STATUS: {holding_status}", (10, 455), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, memory_count, (10, 475), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.cam_label.config(image=img, text="")
            self.cam_label.image = img
        self.after(50, self.update_camera_feed)

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
