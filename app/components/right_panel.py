import tkinter as tk
from app.theme import Theme

class RightPanel(tk.Frame):
    def __init__(self, parent, log_queue, reset_robot_callback, send_message_callback):
        super().__init__(parent, bg=Theme.BG)
        self.log_queue = log_queue
        self.reset_robot_callback = reset_robot_callback
        self.send_message_callback = send_message_callback
        
        self.grid(row=0, column=1, sticky="nsew", padx=(16,32), pady=32)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top Bar
        top_bar = tk.Frame(self, bg=Theme.BG)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        tk.Label(top_bar, text="AI Interaction Log", font=Theme.FONT_H1, bg=Theme.BG, fg=Theme.FG).pack(side=tk.LEFT)

        # Log Area - enclosed in a card with solid border
        log_card = tk.Frame(self, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
        log_card.grid(row=1, column=0, sticky="nsew", pady=(0, 24))
        log_card.rowconfigure(0, weight=1)
        log_card.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_card, wrap=tk.WORD, bg=Theme.SURFACE, fg=Theme.FG, 
                                font=Theme.FONT_LOG, highlightthickness=0, relief=tk.FLAT, bd=0, padx=24, pady=24)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure Basic Log Tags
        self.log_text.tag_configure("user", justify="right", foreground=Theme.FG, font=Theme.FONT_LOG_BOLD)
        self.log_text.tag_configure("llm", justify="left", foreground=Theme.FG, font=Theme.FONT_LOG)
        self.log_text.tag_configure("sys", justify="left", foreground=Theme.MUTED_FG, font=Theme.FONT_BODY)

        # Input Area
        input_frame = tk.Frame(self, bg=Theme.BG)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        # Input Entry wrapped in a solid border to look like Shadcn input
        self.input_entry = tk.Entry(input_frame, font=Theme.FONT_LOG, 
                                    bg=Theme.SURFACE, fg=Theme.FG, insertbackground=Theme.FG,
                                    highlightbackground=Theme.BORDER, highlightthickness=1, relief=tk.SOLID, bd=1)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 16), ipady=16)
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        self.send_button = tk.Button(input_frame, text="SEND", font=Theme.FONT_BODY_BOLD,
                                     bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG, relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.send_message_callback(self.input_entry.get().strip()))
        self.send_button.grid(row=0, column=1, sticky="e", ipadx=24, ipady=8)
        self.send_button.bind("<Enter>", lambda e: e.widget.config(background=Theme.PRIMARY_HOVER) if e.widget['state'] != tk.DISABLED else None)
        self.send_button.bind("<Leave>", lambda e: e.widget.config(background=Theme.PRIMARY) if e.widget['state'] != tk.DISABLED else None)

        self.reset_button = tk.Button(input_frame, text="RESET", font=Theme.FONT_BODY_BOLD,
                                      bg=Theme.DANGER, fg="white", activebackground=Theme.DANGER_HOVER, activeforeground="white", relief=tk.FLAT, bd=0, cursor="hand2", command=self.reset_robot_callback)
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(16, 0), ipadx=16, ipady=8)
        self.reset_button.bind("<Enter>", lambda e: e.widget.config(background=Theme.DANGER_HOVER) if e.widget['state'] != tk.DISABLED else None)
        self.reset_button.bind("<Leave>", lambda e: e.widget.config(background=Theme.DANGER) if e.widget['state'] != tk.DISABLED else None)

        self.input_entry.focus()

    def disable_inputs(self, send_text="SEND", reset_text="RESET"):
        self.send_button.config(state=tk.DISABLED, bg=Theme.MUTED_FG, text=send_text)
        self.reset_button.config(state=tk.DISABLED, bg=Theme.MUTED_FG, text=reset_text)
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=Theme.PRIMARY, text="SEND")
        self.reset_button.config(state=tk.NORMAL, bg=Theme.DANGER, text="RESET")
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()
