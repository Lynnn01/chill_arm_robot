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

        # ── Quick Action Macro Bar Header & Collapsible Panel ──────────────
        self.macro_visible = True

        toggle_frame = tk.Frame(self, bg=Theme.BG)
        toggle_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        toggle_frame.columnconfigure(0, weight=1)

        self.toggle_btn = tk.Button(
            toggle_frame,
            text="⚡ คำสั่งลัด (Quick Macros) ▲ พับเก็บ",
            font=("Leelawadee UI", 10, "bold"),
            bg=Theme.SURFACE,
            fg=Theme.ACCENT,
            activebackground=Theme.SURFACE_MUTED,
            activeforeground=Theme.ACCENT,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=8,
            pady=4
        )
        self.toggle_btn.grid(row=0, column=0, sticky="ew")

        self.macro_bar = tk.Frame(self, bg=Theme.BG)
        self.macro_bar.grid(row=3, column=0, sticky="ew", pady=(0, Theme.SP_SM))

        def _toggle_macro_bar():
            if self.macro_visible:
                self.macro_bar.grid_remove()
                self.toggle_btn.config(text="⚡ คำสั่งลัด (Quick Macros) ▼ ขยายออก")
                self.macro_visible = False
            else:
                self.macro_bar.grid()
                self.toggle_btn.config(text="⚡ คำสั่งลัด (Quick Macros) ▲ พับเก็บ")
                self.macro_visible = True

        self.toggle_btn.config(command=_toggle_macro_bar)

        def _send_macro(cmd_text):
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, cmd_text)
            self._on_send()

        macro_font = ("Leelawadee UI", 11, "bold")

        # Row 1
        r1_frame = tk.Frame(self.macro_bar, bg=Theme.BG)
        r1_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        b1 = RoundedButton(r1_frame, text="🧹 จัดโต๊ะทำงาน",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("จัดโต๊ะทำงานเรียงกล่องเก็บเข้ามุมให้อัตโนมัติ"),
                           height=40)
        b1.pack(side=tk.LEFT, padx=(0, 6), expand=True, fill=tk.X)

        b2 = RoundedButton(r1_frame, text="🧱 ซ้อนกล่อง 3 ชั้น",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("หยิบกล่องสีแดง สีเหลือง สีน้ำเงิน ซ้อนกันบนกล่องสีเขียว"),
                           height=40)
        b2.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Row 2
        r2_frame = tk.Frame(self.macro_bar, bg=Theme.BG)
        r2_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        b3 = RoundedButton(r2_frame, text="💃 เต้นฉลองดีใจ",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("เต้นฉลองดีใจหน่อย"),
                           height=40)
        b3.pack(side=tk.LEFT, padx=(0, 6), expand=True, fill=tk.X)

        b4 = RoundedButton(r2_frame, text="📦 เอาของมาโชว์",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("หยิบกล่องสีแดงมาโชว์"),
                           height=40)
        b4.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Row 3
        r3_frame = tk.Frame(self.macro_bar, bg=Theme.BG)
        r3_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        b5 = RoundedButton(r3_frame, text="👋 โบกมือทักทาย",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("โบกมือทักทายหน่อย"),
                           height=40)
        b5.pack(side=tk.LEFT, padx=(0, 6), expand=True, fill=tk.X)

        b6 = RoundedButton(r3_frame, text="🙇‍♂️ โค้งคำนับ",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("โค้งคำนับต้อนรับ"),
                           height=40)
        b6.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Row 4
        r4_frame = tk.Frame(self.macro_bar, bg=Theme.BG)
        r4_frame.pack(side=tk.TOP, fill=tk.X)

        b7 = RoundedButton(r4_frame, text="🔄 หมุนข้อมือ",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.SURFACE_MUTED, fg=Theme.FG,
                           hover_bg=Theme.ACCENT,
                           font=macro_font,
                           command=lambda: _send_macro("หมุนข้อมือโชว์แป๊บ"),
                           height=40)
        b7.pack(side=tk.LEFT, padx=(0, 6), expand=True, fill=tk.X)

        b8 = RoundedButton(r4_frame, text="✌️ เป่ายิงฉุบ",
                           radius=Theme.RADIUS_SM,
                           bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG,
                           hover_bg=Theme.PRIMARY_HOVER,
                           font=macro_font,
                           command=lambda: _send_macro("มาเป่ายิงฉุบกัน"),
                           height=40)
        b8.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # ── Input bar ──────────────────────────────────────────────────
        bar = tk.Frame(self, bg=Theme.BG)
        bar.grid(row=4, column=0, sticky="ew")
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
                              
        def _on_key(event):
            # Check for Ctrl+V: state 4 is Ctrl, keycode 86 is 'V' key on Windows
            if (event.state & 0x0004) and (event.keycode == 86 or event.keysym.lower() == 'v'):
                try:
                    text = self.input_entry.clipboard_get()
                    try:
                        self.input_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        pass
                    self.input_entry.insert(tk.INSERT, text)
                    return "break"
                except tk.TclError:
                    pass
                
        self.input_entry.bind("<Key>", _on_key)

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

    def _set_mic_off(self):
        self.mic_on = False
        self.is_recording = False
        self.mic_btn.set_text("🔴 Mic: OFF")
        self.mic_btn.set_colors(bg=Theme.DANGER, fg=Theme.PRIMARY_FG, hover_bg=Theme.DANGER_HOVER)

    def _stop_mic_auto(self):
        self._set_mic_off()

    def _toggle_mic(self):
        if not self.mic_on:
            self.mic_on = True
            self.is_recording = True
            self.mic_btn.set_text("🟢 Mic: ON")
            self.mic_btn.set_colors(bg=Theme.SUCCESS, fg=Theme.PRIMARY_FG, hover_bg="#16A34A")
            threading.Thread(target=self._run_speech_recognition, daemon=True).start()
        else:
            self._set_mic_off()

    def _run_speech_recognition(self):
        import speech_recognition as sr
        
        r = sr.Recognizer()
        r.energy_threshold = 250          # Low threshold so quiet initial consonants ('ส', 'ค', 'ต') are captured
        r.dynamic_energy_threshold = False# Keep fixed sensitivity so room noise doesn't delay cutoff
        r.pause_threshold = 0.8           # Fast 0.8s silence threshold — stops listening immediately after speaking
        r.phrase_threshold = 0.1          # Instant 0.1s speech onset detection
        r.non_speaking_duration = 0.4     # 0.4s buffer around speech to keep head & tail syllables
        
        audio = None
        try:
            with sr.Microphone() as source:
                self.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.after(0, lambda: self.input_entry.insert(0, "🎙️ กำลังฟัง... (พูดได้เลย)"))
                
                audio = r.listen(source, timeout=5, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            print("Listening timed out.")
        except Exception as e:
            print(f"Microphone error: {e}")
        finally:
            self.after(0, self._set_mic_off)
            
        if audio:
            self._process_stt_google(audio)
        else:
            self.after(0, lambda: self.input_entry.delete(0, tk.END))
            self.after(0, lambda: self.input_entry.insert(0, ""))

    def _process_stt_google(self, audio):
        import speech_recognition as sr
        r = sr.Recognizer()
        
        self.after(0, lambda: self.input_entry.delete(0, tk.END))
        self.after(0, lambda: self.input_entry.insert(0, "Converting (Google)..."))
        self.after(0, lambda: self.disable_inputs(send_text="STT..."))
            
        try:
            text = r.recognize_google(audio, language="th-TH")
            text = text.strip()
            
            if text:
                self.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.after(0, lambda: self.input_entry.insert(0, text))
                self.after(0, self.enable_inputs)
                if self.send_message_callback:
                    self.send_message_callback(text)
            else:
                self.after(0, lambda: self.input_entry.delete(0, tk.END))
                self.after(0, lambda: self.input_entry.insert(0, "..."))
                self.after(0, self.enable_inputs)
                    
        except sr.UnknownValueError:
            print("Google could not understand audio")
            self.after(0, lambda: self.input_entry.delete(0, tk.END))
            self.after(0, lambda: self.input_entry.insert(0, "..."))
            self.after(0, self.enable_inputs)
        except sr.RequestError as e:
            print(f"Could not request results from Google; {e}")
            self.after(0, lambda: self.input_entry.delete(0, tk.END))
            self.after(0, lambda: self.input_entry.insert(0, f"STT Error: {e}"))
            self.after(0, self.enable_inputs)

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
