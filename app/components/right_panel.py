"""
app/components/right_panel.py — Chat log, input bar, SEND / RESET
"""
import tkinter as tk
import time
import queue
import threading
import sounddevice as sd
import numpy as np
from app.theme import Theme
from app.widgets import RoundedButton, RoundedFrame


class RightPanel(tk.Frame):
    def __init__(self, parent, log_queue, reset_robot_callback, send_message_callback):
        super().__init__(parent, bg=Theme.BG)
        self.log_queue = log_queue
        self.reset_robot_callback = reset_robot_callback
        self.send_message_callback = send_message_callback
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.recorded_frames = []
        self.sample_rate = 16000

        self.grid(row=0, column=1, sticky="nsew",
                  padx=Theme.SP_XL, pady=Theme.SP_XL)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Header ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=Theme.BG)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, Theme.SP_MD))
        tk.Label(hdr, text="AI Interaction Log",
                 font=Theme.FONT_H1, bg=Theme.BG, fg=Theme.FG).pack(side=tk.LEFT)
        
        self.mic_on = False
        self.speaker_on = False

        self.mic_btn = RoundedButton(hdr, text="🔇 Mic: OFF",
                                     radius=Theme.RADIUS_SM,
                                     bg=Theme.DANGER, fg=Theme.PRIMARY_FG,
                                     hover_bg=Theme.BORDER,
                                     font=Theme.FONT_BODY,
                                     command=self._toggle_mic,
                                     width=100, height=30)
        self.mic_btn.pack(side=tk.RIGHT, padx=Theme.SP_SM)

        self.speaker_btn = RoundedButton(hdr, text="🔈 Spk: OFF",
                                         radius=Theme.RADIUS_SM,
                                         bg=Theme.DANGER, fg=Theme.PRIMARY_FG,
                                         hover_bg=Theme.BORDER,
                                         font=Theme.FONT_BODY,
                                         command=self._toggle_speaker,
                                         width=100, height=30)
        self.speaker_btn.pack(side=tk.RIGHT, padx=Theme.SP_SM)

        tk.Label(hdr, text="● Live",
                 font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.SUCCESS).pack(side=tk.RIGHT, padx=Theme.SP_MD)

        # Mode Selector
        self.current_mode = tk.StringVar(value="ARM Mode")
        modes = ["ARM Mode", "Person Detect", "Face Detect", "Cube Detect"]
        self.mode_menu = tk.OptionMenu(hdr, self.current_mode, *modes, command=self._on_mode_change)
        self.mode_menu.config(
            bg=Theme.SURFACE, fg=Theme.FG, 
            activebackground=Theme.BORDER, activeforeground=Theme.FG,
            font=Theme.FONT_BODY, highlightthickness=0, bd=0, relief=tk.FLAT
        )
        self.mode_menu["menu"].config(
            bg=Theme.SURFACE, fg=Theme.FG, 
            activebackground=Theme.BORDER, activeforeground=Theme.FG,
            font=Theme.FONT_BODY, bd=0
        )
        self.mode_menu.pack(side=tk.RIGHT, padx=Theme.SP_MD)

        # ── Log card ───────────────────────────────────────────────────
        self.log_card = RoundedFrame(self, radius=Theme.RADIUS_LG,
                                     bg=Theme.SURFACE, border_color=Theme.BORDER)
        self.log_card.grid(row=1, column=0, sticky="nsew", pady=(0, Theme.SP_MD))
        self.log_card.inner.rowconfigure(0, weight=1)
        self.log_card.inner.columnconfigure(0, weight=1)

        self.log_text = tk.Text(self.log_card.inner, wrap=tk.WORD,
                                bg=Theme.SURFACE, fg=Theme.FG,
                                font=Theme.FONT_LOG,
                                highlightthickness=0, relief=tk.FLAT, bd=0,
                                padx=Theme.SP_LG, pady=Theme.SP_LG,
                                state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scroll = tk.Scrollbar(self.log_card.inner, orient=tk.VERTICAL,
                              command=self.log_text.yview, width=6)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scroll.set)

        # text tags
        self.log_text.tag_configure("user",
                                    justify="right",
                                    foreground=Theme.ACCENT,
                                    font=Theme.FONT_LOG_BOLD)
        self.log_text.tag_configure("llm",
                                    justify="left",
                                    foreground=Theme.FG,
                                    font=Theme.FONT_LOG)
        self.log_text.tag_configure("sys",
                                    justify="left",
                                    foreground=Theme.CAPTION_FG,
                                    font=Theme.FONT_BODY)

        # ── Input bar ──────────────────────────────────────────────────
        bar = tk.Frame(self, bg=Theme.BG)
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)

        # Entry wrapped in a RoundedFrame for perfect height matching
        # Use SURFACE_MUTED for a modern "filled" input look
        self.input_wrap = RoundedFrame(bar, radius=Theme.RADIUS_MD,
                                       bg=Theme.SURFACE_MUTED, border_color=Theme.SURFACE_MUTED)
        self.input_wrap.grid(row=0, column=0, sticky="ew",
                             padx=(0, Theme.SP_SM))
        self.input_wrap.config(height=48)
        self.input_wrap.grid_propagate(False)
        self.input_wrap.inner.columnconfigure(0, weight=1)
        self.input_wrap.inner.rowconfigure(0, weight=1)
        self.input_wrap.inner.config(bg=Theme.SURFACE_MUTED)

        self.input_entry = tk.Entry(self.input_wrap.inner,
                                    font=Theme.FONT_LOG,
                                    bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                                    insertbackground=Theme.FG,
                                    relief=tk.FLAT, bd=0,
                                    highlightthickness=0)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=16)

        self.input_entry.bind("<Return>",
                              lambda e: self._on_send())
        self.input_entry.bind("<FocusIn>",
                              lambda e: self.input_wrap.configure_colors(border_color=Theme.BORDER_FOCUS))
        self.input_entry.bind("<FocusOut>",
                              lambda e: self.input_wrap.configure_colors(border_color=Theme.SURFACE_MUTED))

        # SEND button
        self.send_btn = RoundedButton(bar, text="SEND",
                                      radius=Theme.RADIUS_SM,
                                      bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG,
                                      hover_bg=Theme.PRIMARY_HOVER,
                                      font=Theme.FONT_BODY_BOLD,
                                      command=self._on_send,
                                      width=90, height=48)
        self.send_btn.grid(row=0, column=1, padx=(0, Theme.SP_SM))

        # RESET button
        self.reset_btn = RoundedButton(bar, text="RESET",
                                       radius=Theme.RADIUS_SM,
                                       bg=Theme.DANGER, fg=Theme.DANGER_FG,
                                       hover_bg=Theme.DANGER_HOVER,
                                       font=Theme.FONT_BODY_BOLD,
                                       command=self.reset_robot_callback,
                                       width=90, height=48)
        self.reset_btn.grid(row=0, column=2)

        self.input_entry.focus()

    # ------------------------------------------------------------------
    def _on_send(self):
        self.send_message_callback(self.input_entry.get().strip())

    def disable_inputs(self, send_text="SEND", reset_text="RESET"):
        self.send_btn.set_text(send_text)
        self.send_btn.set_state(tk.DISABLED)
        self.reset_btn.set_text(reset_text)
        self.reset_btn.set_state(tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)

    def enable_inputs(self):
        self.send_btn.set_text("SEND")
        self.send_btn.set_state(tk.NORMAL)
        self.reset_btn.set_text("RESET")
        self.reset_btn.set_state(tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()

    def _stop_mic_auto(self):
        if self.mic_on:
            self._toggle_mic()

    def _toggle_mic(self):
        self.mic_on = not self.mic_on
        if self.mic_on:
            self.mic_btn.set_text("🔴 Mic: REC")
            self.mic_btn.set_colors(bg=Theme.WARNING, fg=Theme.PRIMARY_FG)
            self.is_recording = True
            threading.Thread(target=self._run_speech_recognition, daemon=True).start()
        else:
            self.mic_btn.set_text("🔇 Mic: OFF")
            self.mic_btn.set_colors(bg=Theme.DANGER, fg=Theme.PRIMARY_FG)
            self.is_recording = False

    def _run_speech_recognition(self):
        import speech_recognition as sr
        
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        
        audio = None
        try:
            with sr.Microphone() as source:
                # Instantly update UI and start listening without ambient noise delay
                if hasattr(self, 'window') and self.window:
                    self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                    self.window.after(0, lambda: self.input_entry.insert(0, "Listening..."))
                
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("Listening timed out.")
        except Exception as e:
            print(f"Microphone error: {e}")
            
        if hasattr(self, 'window') and self.window:
            self.window.after(0, self._stop_mic_auto)
            
        if audio:
            self._process_stt_google(audio)
        else:
            if hasattr(self, 'window') and self.window:
                self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.window.after(0, lambda: self.input_entry.insert(0, "..."))

    def _process_stt_google(self, audio):
        import speech_recognition as sr
        r = sr.Recognizer()
        
        if hasattr(self, 'window') and self.window:
            self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
            self.window.after(0, lambda: self.input_entry.insert(0, "Converting (Google)..."))
            self.window.after(0, lambda: self.disable_inputs(send_text="STT..."))
            
        try:
            text = r.recognize_google(audio, language="th-TH")
            text = text.strip()
            
            if text:
                if hasattr(self, 'window') and self.window:
                    self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                    self.window.after(0, lambda: self.input_entry.insert(0, text))
                    self.window.after(0, self.enable_inputs)
                if self.send_message_callback:
                    self.send_message_callback(text)
            else:
                if hasattr(self, 'window') and self.window:
                    self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                    self.window.after(0, lambda: self.input_entry.insert(0, "..."))
                    self.window.after(0, self.enable_inputs)
                    
        except sr.UnknownValueError:
            print("Google could not understand audio")
            if hasattr(self, 'window') and self.window:
                self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.window.after(0, lambda: self.input_entry.insert(0, "..."))
                self.window.after(0, self.enable_inputs)
        except sr.RequestError as e:
            print(f"Could not request results from Google; {e}")
            if hasattr(self, 'window') and self.window:
                self.window.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.window.after(0, lambda: self.input_entry.insert(0, f"STT Error: {e}"))
                self.window.after(0, self.enable_inputs)

    def _toggle_speaker(self):
        self.speaker_on = not self.speaker_on
        if self.speaker_on:
            self.speaker_btn.set_text("🔊 Spk: ON")
            self.speaker_btn.set_colors(bg=Theme.SUCCESS, fg=Theme.PRIMARY_FG)
        else:
            self.speaker_btn.set_text("🔈 Spk: OFF")
            self.speaker_btn.set_colors(bg=Theme.DANGER, fg=Theme.PRIMARY_FG)

    def _on_mode_change(self, new_mode):
        self.log_queue.put(f"⚙️ <SYSTEM>: Switched to {new_mode} mode")
        try:
            from vision.tools.manager import set_detect_mode
            set_detect_mode(new_mode)
        except Exception as e:
            print(f"⚠️ Error changing mode: {e}")
