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
        self._pending_image = None  # Thread-safe image transfer slot
        
        self.grid(row=0, column=0, sticky="nsew", padx=(30,15), pady=30)
        self.columnconfigure(0, weight=1)

        # Title
        tk.Label(self, text="ONE ARM", font=("Tahoma", 28, "bold"),
                 bg=self.theme["bg"], fg=self.theme["btn_bg"]).grid(
                     row=0, column=0, sticky="w", pady=(0, 20))
        
        # Camera Feed
        self.cam_label = tk.Label(self, bg=self.theme["frame"],
                                   text="Camera Offline", fg=self.theme["fg"],
                                   font=("Tahoma", 14), width=60, height=20,
                                   relief=tk.FLAT)
        self.cam_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.theme["bg"], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.theme["frame"],
                        foreground=self.theme["fg"], font=("Tahoma", 12, "bold"),
                        padding=[20, 10], borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', self.theme["btn_bg"])],
                  foreground=[('selected', self.theme["btn_fg"])])

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.rowconfigure(2, weight=1)

        # --- Tab 1: Control ---
        self.tab_control = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_control, text='Control')

        self.dash_frame = tk.Frame(self.tab_control, bg=self.theme["frame"])
        self.dash_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(self.dash_frame, text=" Live Robot Status ",
                 font=("Tahoma", 14, "bold"),
                 bg=self.theme["frame"], fg=self.theme["fg"]).grid(
                     row=0, column=0, columnspan=6, pady=(15, 10))
        
        for i, axis in enumerate(["X", "Y", "Z", "Rx", "Ry", "Rz"]):
            tk.Label(self.dash_frame, text=f"{axis}:",
                     font=("Tahoma", 12, "bold"),
                     bg=self.theme["frame"], fg=self.theme["fg"]).grid(
                         row=(i//3)+1, column=(i%3)*2,
                         sticky="e", padx=(25, 5), pady=15)
            
            lbl_val = tk.Label(self.dash_frame, text="---",
                                font=("Tahoma", 12),
                                bg=self.theme["dash_bg"], fg=self.theme["fg"],
                                width=8, anchor="center")
            lbl_val.grid(row=(i//3)+1, column=(i%3)*2+1, sticky="w")
            self.status_labels[axis] = lbl_val

        self.qa_frame = tk.Frame(self.tab_control, bg=self.theme["bg"])
        self.qa_frame.pack(fill=tk.X)
        
        def on_enter(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_hover"]
        def on_leave(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_bg"]

        btn_cfg = {"font": ("Tahoma", 14, "bold"), "bg": self.theme["btn_bg"],
                   "fg": self.theme["btn_fg"], "relief": tk.FLAT, "cursor": "hand2"}
        
        for text, cmd in [("👋 โบกมือ", "โบกมือทักทายหน่อย"),
                           ("👐 เปิดจับ", "เปิดหัวจับ"),
                           ("✊ ปิดจับ", "ปิดหัวจับ"),
                           ("🕺 เต้น", "เต้นให้ดูหน่อย")]:
            b = tk.Button(self.qa_frame, text=text,
                          command=lambda c=cmd: self.run_quick_action(c), **btn_cfg)
            b.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True, ipady=10)
            b.bind("<Enter>", on_enter)
            b.bind("<Leave>", on_leave)
            self.qa_btns.append(b)

        # --- Tab 2: Calibration ---
        self.tab_calib = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_calib, text='Calibration')

        calib_frame = tk.Frame(self.tab_calib, bg=self.theme["frame"])
        calib_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(calib_frame, text=" Camera to Robot Offsets ",
                 font=("Tahoma", 14, "bold"),
                 bg=self.theme["frame"], fg=self.theme["fg"]).grid(
                     row=0, column=0, columnspan=2, pady=(15, 10))

        import json
        try:
            from hardware.init import CONFIG_PATH
            with open(CONFIG_PATH, "r") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {"x": 0, "y": 0, "z": 0}

        self.calib_vars = {}
        for i, axis in enumerate(["x", "y", "z"]):
            tk.Label(calib_frame, text=f"Offset {axis.upper()}:",
                     font=("Tahoma", 12, "bold"),
                     bg=self.theme["frame"], fg=self.theme["fg"]).grid(
                         row=i+1, column=0, sticky="e", padx=(25, 5), pady=15)
            var = tk.DoubleVar(value=config_data.get(axis, 0))
            tk.Entry(calib_frame, textvariable=var, font=("Tahoma", 12),
                     bg=self.theme["dash_bg"], fg=self.theme["fg"],
                     width=15, insertbackground=self.theme["fg"],
                     relief=tk.FLAT).grid(row=i+1, column=1, sticky="w", pady=15)
            self.calib_vars[axis] = var
            
        btn_save = tk.Button(calib_frame, text="Save Calibration",
                             font=("Tahoma", 12, "bold"),
                             bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
                             relief=tk.FLAT, cursor="hand2",
                             command=self.save_calibration)
        btn_save.grid(row=4, column=0, columnspan=2, pady=20, ipadx=15, ipady=10)
        btn_save.bind("<Enter>", on_enter)
        btn_save.bind("<Leave>", on_leave)
        
        # --- Tab 3: Memory ---
        self.tab_memory = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(self.tab_memory, text='Memory')
        
        self.memory_text = tk.Text(self.tab_memory, wrap=tk.WORD,
                                    bg=self.theme["dash_bg"], fg=self.theme["fg"],
                                    font=("Tahoma", 12), bd=0, relief=tk.FLAT,
                                    padx=15, pady=15)
        self.memory_text.pack(fill=tk.BOTH, expand=True, pady=20)
        self.memory_text.config(state=tk.DISABLED)

        # Start loops
        self._start_camera_processor()
        self._start_dashboard_loop()
        self._update_memory_ui()

    # ── Buttons ──────────────────────────────────────────────────────────────

    def disable_buttons(self):
        for b in self.qa_btns:
            b.config(state=tk.DISABLED, bg="#555555")

    def enable_buttons(self):
        for b in self.qa_btns:
            b.config(state=tk.NORMAL, bg=self.theme["btn_bg"])

    # ── Camera Feed ──────────────────────────────────────────────────────────

    def _start_camera_processor(self):
        """
        Image processing runs in a background thread to avoid blocking the UI.
        Processed PIL images are placed in _pending_image; the Tk after() loop
        picks them up safely on the main thread.
        """
        self._pending_image = None

        def _process_loop():
            while True:
                try:
                    raw = cam_manager.get_frame()
                    if raw is not None and raw.size > 0:
                        rgb = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
                        resized = cv2.resize(rgb, (480, 360))
                        self._pending_image = Image.fromarray(resized)
                except Exception:
                    pass
                import time
                time.sleep(0.05)

        threading.Thread(target=_process_loop, daemon=True).start()
        self._apply_camera_frame()   # start Tk polling

    def _apply_camera_frame(self):
        """Called on the main Tk thread every 50ms — only does Tkinter work."""
        img = self._pending_image
        if img is not None:
            self._pending_image = None
            if not hasattr(self, 'tk_image'):
                self.tk_image = ImageTk.PhotoImage(image=img)
                self.cam_label.config(image=self.tk_image, text="")
            else:
                self.tk_image.paste(img)
        self.after(50, self._apply_camera_frame)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _start_dashboard_loop(self):
        """One persistent thread fetches coordinates; posts updates via log_queue."""
        def _loop():
            import time
            import hardware.init as hw
            while True:
                try:
                    coords = hw.mc.get_coords()
                    if coords and len(coords) >= 6:
                        hw.last_coords = coords
                        def _update(c=coords):
                            for ax, val in zip(["X", "Y", "Z", "Rx", "Ry", "Rz"], c):
                                if ax in self.status_labels:
                                    self.status_labels[ax].config(text=f"{val:.1f}")
                        self.log_queue.put(_update)
                except Exception:
                    pass
                time.sleep(0.5)
        threading.Thread(target=_loop, daemon=True).start()

    # ── Memory Tab ────────────────────────────────────────────────────────────

    def _update_memory_ui(self):
        """Runs on the main thread via after()."""
        try:
            import hardware.init as hw
            lines = ["🧠 Known Objects:\n"]
            if hw.known_objects:
                for obj, coords in hw.known_objects.items():
                    if isinstance(coords, list):
                        lines.append(f" 🔹 {obj}: [X: {coords[0]:.1f}, Y: {coords[1]:.1f}]")
                    else:
                        lines.append(f" 🔹 {obj}: {coords}")
            else:
                lines.append("   (Empty)")
            lines.append(f"\n🖐️ Gripper Status:\n")
            if hw.is_holding_object:
                lines.append(f" 🔸 Holding: {hw.current_held_object}")
            else:
                lines.append(" 🔸 Empty")
            
            self.memory_text.config(state=tk.NORMAL)
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.insert(tk.END, "\n".join(lines))
            self.memory_text.config(state=tk.DISABLED)
        except Exception:
            pass
        self.after(1000, self._update_memory_ui)

    # ── Calibration ───────────────────────────────────────────────────────────

    def save_calibration(self):
        import json
        from hardware.init import CONFIG_PATH
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        for axis in ["x", "y", "z"]:
            data[axis] = self.calib_vars[axis].get()
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print("\n✅ <SYSTEM>: Calibration settings saved to config.json")
