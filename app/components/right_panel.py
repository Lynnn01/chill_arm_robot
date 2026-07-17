import tkinter as tk
import threading
import speech_recognition as sr

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
                                font=("Tahoma", 12), highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"], 
                                highlightthickness=2, relief=tk.FLAT, bd=0, padx=15, pady=15)
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(0, 20))

        # Input Area
        input_frame = tk.Frame(self, bg=self.theme["bg"])
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        self.voice_btn = tk.Button(input_frame, text="🎙️", font=("Tahoma", 14), bg="#ff9900", fg="white", relief=tk.FLAT, cursor="hand2", command=self.record_voice)
        self.voice_btn.grid(row=0, column=0, sticky="w", padx=(0, 10), ipadx=10, ipady=8)

        self.input_entry = tk.Entry(input_frame, font=("Tahoma", 14), 
                                    bg=self.theme["frame"], fg=self.theme["fg"], insertbackground=self.theme["fg"],
                                    highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"], 
                                    highlightthickness=2, relief=tk.FLAT, bd=0)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), ipady=12)
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        self.send_button = tk.Button(input_frame, text="SEND", font=("Tahoma", 12, "bold"),
                                     bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.send_message_callback(self.input_entry.get().strip()))
        self.send_button.grid(row=0, column=2, sticky="e", ipadx=20, ipady=10)

        self.reset_button = tk.Button(input_frame, text="RESET", font=("Tahoma", 12, "bold"),
                                      bg="#FF3333", fg="white", activebackground="#CC0000", activeforeground="white", relief=tk.FLAT, bd=0, cursor="hand2", command=self.reset_robot_callback)
        self.reset_button.grid(row=0, column=3, sticky="e", padx=(10, 0), ipadx=15, ipady=10)

        self.input_entry.focus()

    def record_voice(self):
        def _listen():
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                def _notify():
                    self.input_entry.delete(0, tk.END)
                    self.input_entry.insert(0, "🎙️ กำลังฟังเสียง... พูดได้เลยครับ")
                    self.voice_btn.config(bg="#cc0000")
                self.log_queue.put(_notify)
                
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio, language="th-TH")
                    def _done():
                        self.input_entry.delete(0, tk.END)
                        self.input_entry.insert(0, text)
                        self.voice_btn.config(bg="#ff9900")
                        self.send_message_callback(text)
                    self.log_queue.put(_done)
                except Exception as e:
                    def _err():
                        self.input_entry.delete(0, tk.END)
                        print(f"\n⚠️ <SYSTEM>: Voice recognition error / no speech detected.")
                        self.voice_btn.config(bg="#ff9900")
                        self.enable_inputs()
                    self.log_queue.put(_err)

        self.disable_inputs()
        threading.Thread(target=_listen, daemon=True).start()

    def disable_inputs(self):
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.reset_button.config(state=tk.DISABLED, bg="#666666")
        self.voice_btn.config(state=tk.DISABLED, bg="#666666")
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.theme["btn_bg"])
        self.reset_button.config(state=tk.NORMAL, bg="#FF3333")
        self.voice_btn.config(state=tk.NORMAL, bg="#ff9900")
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()
