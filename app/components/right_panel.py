import tkinter as tk
import threading

class RightPanel(tk.Frame):
    def __init__(self, parent, theme, log_queue, toggle_theme_callback, reset_robot_callback, send_message_callback):
        super().__init__(parent, bg=theme["bg"])
        self.theme = theme
        self.log_queue = log_queue
        self.toggle_theme_callback = toggle_theme_callback
        self.reset_robot_callback = reset_robot_callback
        self.send_message_callback = send_message_callback
        
        self.grid(row=0, column=1, sticky="nsew", padx=(10,30), pady=30)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top Bar (Dark Mode Toggle)
        top_bar = tk.Frame(self, bg=self.theme["bg"])
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.theme_btn = tk.Button(top_bar, text="🌗 Dark Mode", command=self.toggle_theme_callback, font=("Tahoma", 10, "bold"), bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT, ipadx=10, ipady=5)

        # Log Area
        self.log_text = tk.Text(self, wrap=tk.WORD, bg=self.theme["frame"], fg=self.theme["fg"], 
                                font=("Tahoma", 14), highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"], 
                                highlightthickness=2, relief=tk.FLAT, bd=0, padx=15, pady=15)
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # Configure Basic Log Tags
        self.log_text.tag_configure("user", justify="right", foreground="#0078D7", font=("Tahoma", 12, "bold"))
        self.log_text.tag_configure("llm", justify="left", foreground=self.theme["fg"], font=("Tahoma", 12))
        self.log_text.tag_configure("sys", justify="left", foreground="#888888", font=("Tahoma", 10, "italic"))

        # Input Area
        input_frame = tk.Frame(self, bg=self.theme["bg"])
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(2, weight=1)

        # Input Area Buttons
        self.input_entry = tk.Entry(input_frame, font=("Tahoma", 14), 
                                    bg=self.theme["frame"], fg=self.theme["fg"], insertbackground=self.theme["fg"],
                                    highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"], 
                                    highlightthickness=2, relief=tk.FLAT, bd=0)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=12)
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        self.send_button = tk.Button(input_frame, text="SEND", font=("Tahoma", 12, "bold"),
                                     bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.send_message_callback(self.input_entry.get().strip()))
        self.send_button.grid(row=0, column=1, sticky="e", ipadx=20, ipady=10)

        self.reset_button = tk.Button(input_frame, text="RESET", font=("Tahoma", 12, "bold"),
                                      bg="#FF3333", fg="white", activebackground="#CC0000", activeforeground="white", relief=tk.FLAT, bd=0, cursor="hand2", command=self.reset_robot_callback)
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(10, 0), ipadx=15, ipady=10)

        input_frame.columnconfigure(0, weight=1)

        self.input_entry.focus()

    def disable_inputs(self):
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.reset_button.config(state=tk.DISABLED, bg="#666666")
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.theme["btn_bg"])
        self.reset_button.config(state=tk.NORMAL, bg="#FF3333")
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()
