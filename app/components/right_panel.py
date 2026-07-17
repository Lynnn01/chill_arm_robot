import tkinter as tk

class RightPanel(tk.Frame):
    def __init__(self, parent, theme, log_queue, reset_robot_callback, send_message_callback):
        super().__init__(parent, bg=theme["bg"])
        self.theme = theme
        self.log_queue = log_queue
        self.reset_robot_callback = reset_robot_callback
        self.send_message_callback = send_message_callback
        
        self.grid(row=0, column=1, sticky="nsew", padx=(15,30), pady=30)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        def on_enter_btn(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_hover"]
        def on_leave_btn(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["btn_bg"]
                
        def on_enter_danger(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["danger_hover"]
        def on_leave_danger(e):
            if e.widget['state'] != tk.DISABLED:
                e.widget['background'] = self.theme["danger"]

        # Top Bar
        top_bar = tk.Frame(self, bg=self.theme["bg"])
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        tk.Label(top_bar, text="AI Interaction Log", font=("Tahoma", 16, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(side=tk.LEFT)

        # Log Area
        self.log_text = tk.Text(self, wrap=tk.WORD, bg=self.theme["frame"], fg=self.theme["fg"], 
                                font=("Tahoma", 14), highlightthickness=0, relief=tk.FLAT, bd=0, padx=20, pady=20)
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # Configure Basic Log Tags
        self.log_text.tag_configure("user", justify="right", foreground="#3B8ED0", font=("Tahoma", 14, "bold"))
        self.log_text.tag_configure("llm", justify="left", foreground=self.theme["fg"], font=("Tahoma", 14))
        self.log_text.tag_configure("sys", justify="left", foreground="#888888", font=("Tahoma", 12, "italic"))

        # Input Area
        input_frame = tk.Frame(self, bg=self.theme["bg"])
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        # Input Area Buttons
        self.input_entry = tk.Entry(input_frame, font=("Tahoma", 16), 
                                    bg=self.theme["frame"], fg=self.theme["fg"], insertbackground=self.theme["fg"],
                                    highlightthickness=0, relief=tk.FLAT, bd=0)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15), ipady=15)
        # Internal padding for entry using a small hack
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        self.send_button = tk.Button(input_frame, text="SEND", font=("Tahoma", 14, "bold"),
                                     bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.send_message_callback(self.input_entry.get().strip()))
        self.send_button.grid(row=0, column=1, sticky="e", ipadx=25, ipady=12)
        self.send_button.bind("<Enter>", on_enter_btn)
        self.send_button.bind("<Leave>", on_leave_btn)

        self.reset_button = tk.Button(input_frame, text="RESET", font=("Tahoma", 14, "bold"),
                                      bg=self.theme["danger"], fg="white", activebackground=self.theme["danger_hover"], activeforeground="white", relief=tk.FLAT, bd=0, cursor="hand2", command=self.reset_robot_callback)
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(15, 0), ipadx=20, ipady=12)
        self.reset_button.bind("<Enter>", on_enter_danger)
        self.reset_button.bind("<Leave>", on_leave_danger)

        self.input_entry.focus()

    def disable_inputs(self):
        self.send_button.config(state=tk.DISABLED, bg="#555555")
        self.reset_button.config(state=tk.DISABLED, bg="#555555")
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.theme["btn_bg"])
        self.reset_button.config(state=tk.NORMAL, bg=self.theme["danger"])
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()
