import tkinter as tk
import customtkinter as ctk
import threading

class RightPanel(ctk.CTkFrame):
    def __init__(self, parent, log_queue, toggle_theme_callback, reset_robot_callback, send_message_callback):
        super().__init__(parent, fg_color="transparent")
        
        self.log_queue = log_queue
        self.toggle_theme_callback = toggle_theme_callback
        self.reset_robot_callback = reset_robot_callback
        self.send_message_callback = send_message_callback
        
        self.grid(row=0, column=1, sticky="nsew", padx=(10,30), pady=30)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top Bar (Dark Mode Toggle)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.theme_btn = ctk.CTkButton(
            top_bar, 
            text="☀️ Light Mode", 
            command=self.toggle_theme_callback, 
            font=("Tahoma", 12, "bold"),
            width=120,
            height=32,
            corner_radius=16,
            fg_color="#333333",
            hover_color="#555555"
        )
        self.theme_btn.pack(side=tk.RIGHT)

        # Log Area
        self.log_text = ctk.CTkTextbox(
            self, 
            wrap=tk.WORD, 
            font=("Tahoma", 14),
            corner_radius=15,
            border_width=2
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # Configure Basic Log Tags
        self.log_text.tag_config("user", justify="right", foreground="#1E90FF", font=("Tahoma", 12, "bold"))
        self.log_text.tag_config("llm", justify="left", font=("Tahoma", 12))
        self.log_text.tag_config("sys", justify="left", foreground="#888888", font=("Tahoma", 10, "italic"))

        # Input Area
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        # Input Entry
        self.input_entry = ctk.CTkEntry(
            input_frame, 
            font=("Tahoma", 14),
            height=45,
            corner_radius=15,
            placeholder_text="พิมพ์คำสั่งให้ AI ที่นี่..."
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        # Send Button
        self.send_button = ctk.CTkButton(
            input_frame, 
            text="SEND", 
            font=("Tahoma", 14, "bold"),
            width=100,
            height=45,
            corner_radius=15,
            command=lambda: self.send_message_callback(self.input_entry.get().strip())
        )
        self.send_button.grid(row=0, column=1, sticky="e")

        # Reset Button
        self.reset_button = ctk.CTkButton(
            input_frame, 
            text="RESET", 
            font=("Tahoma", 14, "bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=100,
            height=45,
            corner_radius=15,
            command=self.reset_robot_callback
        )
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        self.input_entry.focus()

    def disable_inputs(self):
        self.send_button.configure(state=tk.DISABLED, fg_color="#555555")
        self.reset_button.configure(state=tk.DISABLED, fg_color="#555555")
        self.input_entry.configure(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.configure(state=tk.NORMAL, fg_color=["#3B8ED0", "#1F6AA5"])
        self.reset_button.configure(state=tk.NORMAL, fg_color="#E74C3C")
        self.input_entry.configure(state=tk.NORMAL)
        self.input_entry.focus()
