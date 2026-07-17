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
        input_frame.columnconfigure(2, weight=1)

        # Input Area Buttons
        self.mic_btn = tk.Button(input_frame, text="MIC", font=("Tahoma", 12, "bold"), bg=self.theme["bg"], fg="#ff3333", activebackground=self.theme["bg"], activeforeground=self.theme["fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=self.toggle_mic)
        self.mic_btn.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.tts_btn = tk.Button(input_frame, text="SPK", font=("Tahoma", 12, "bold"), bg=self.theme["bg"], fg=self.theme["fg"], activebackground=self.theme["bg"], activeforeground=self.theme["fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=self.toggle_tts)
        self.tts_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))

        self.mic_active = False
        self.tts_active = True
        self.stop_listening = None

        self.input_entry = tk.Entry(input_frame, font=("Tahoma", 14), 
                                    bg=self.theme["frame"], fg=self.theme["fg"], insertbackground=self.theme["fg"],
                                    highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"], 
                                    highlightthickness=2, relief=tk.FLAT, bd=0)
        self.input_entry.grid(row=0, column=2, sticky="ew", padx=(0, 10), ipady=12)
        self.input_entry.bind("<Return>", lambda event: self.send_message_callback(self.input_entry.get().strip()))

        self.send_button = tk.Button(input_frame, text="SEND", font=("Tahoma", 12, "bold"),
                                     bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], relief=tk.FLAT, bd=0, cursor="hand2", command=lambda: self.send_message_callback(self.input_entry.get().strip()))
        self.send_button.grid(row=0, column=3, sticky="e", ipadx=20, ipady=10)

        self.reset_button = tk.Button(input_frame, text="RESET", font=("Tahoma", 12, "bold"),
                                      bg="#FF3333", fg="white", activebackground="#CC0000", activeforeground="white", relief=tk.FLAT, bd=0, cursor="hand2", command=self.reset_robot_callback)
        self.reset_button.grid(row=0, column=4, sticky="e", padx=(10, 0), ipadx=15, ipady=10)

        self.input_entry.focus()

    def toggle_tts(self):
        if self.tts_active:
            self.tts_active = False
            self.tts_btn.config(fg="#ff3333") # Red when muted
        else:
            self.tts_active = True
            self.tts_btn.config(fg=self.theme["fg"]) # Normal when active

    def toggle_mic(self):
        if self.mic_active:
            # Turn OFF mic
            if self.stop_listening:
                self.stop_listening(wait_for_stop=False)
                self.stop_listening = None
            self.mic_active = False
            self.mic_btn.config(fg="#ff3333") # Red when muted
        else:
            # Turn ON mic
            self.mic_active = True
            self.mic_btn.config(fg=self.theme["fg"]) # Normal when active
            
            def _listen_worker():
                recognizer = sr.Recognizer()
                try:
                    source = sr.Microphone()
                    with source:
                        recognizer.adjust_for_ambient_noise(source)
                    
                    def _callback(rec, audio):
                        if not self.mic_active:
                            return
                        try:
                            text = rec.recognize_google(audio, language="th-TH")
                            if text:
                                def _send():
                                    self.send_message_callback(text)
                                self.log_queue.put(_send)
                        except sr.UnknownValueError:
                            pass
                        except Exception as e:
                            print(f"Voice error: {e}")
                    
                    self.stop_listening = recognizer.listen_in_background(source, _callback)
                except Exception as e:
                    def _err():
                        self.mic_active = False
                        self.mic_btn.config(fg="#ff3333")
                        print(f"Mic error: {e}")
                    self.log_queue.put(_err)

            threading.Thread(target=_listen_worker, daemon=True).start()

    def disable_inputs(self):
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.reset_button.config(state=tk.DISABLED, bg="#666666")
        self.mic_btn.config(state=tk.DISABLED)
        self.tts_btn.config(state=tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.theme["btn_bg"])
        self.reset_button.config(state=tk.NORMAL, bg="#FF3333")
        self.mic_btn.config(state=tk.NORMAL)
        self.tts_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()
