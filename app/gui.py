import tkinter as tk
import sys
import threading
import asyncio
import queue

from app.components.left_panel import LeftPanel
from app.components.right_panel import RightPanel
from app.theme import Theme

# Trigger YOLO preload
try:
    import vision.yolo_detector
except Exception:
    pass

AUTO_PROMPTS = [
    # ── วัตถุและการจัดวาง (Safe Pick, Place & Stacking) ──
    "หยิบกล่องสี{color}มาโชว์ให้ดูหน่อย",
    "หยิบกล่องสี{color}แล้วนำไปวางซ้อนบนกล่องใบอื่น",
    "หยิบกล่องสี{color}แล้วย้ายไปวางในตำแหน่งที่ปลอดภัย",
    "หยิบกล่องสี{color}ขึ้นมาโชว์ แล้วเอาไปวางซ้อนให้เรียบร้อย",
    "หยิบกล่องสี{color}ไปวางที่ปลอดภัยแล้วเต้นฉลองหน่อย",
    "หยิบกล่องที่โดนวางทับอยู่ขึ้นมาโชว์หน่อย",
    "แกะกล่องที่โดนซ้อนทับอยู่แล้วนำไปวางในตำแหน่งที่ปลอดภัย",

    # ── วิสัยทัศน์และการสำรวจ (Vision & Safe Inspection) ──
    "อธิบายหน่อยว่าตอนนี้บนโต๊ะมีอะไรบ้าง",
    "ส่ายกล้องสำรวจรอบๆ โต๊ะหน่อย",
    "มองหากล่องสี{color}ให้หน่อยว่าอยู่ตรงไหน",
    "อธิบายหน่อยว่ามีกล่องอะไรซ้อนทับกันอยู่บ้างบนโต๊ะ",
    "สแกนหาตำแหน่งของกล่องสี{color}บนโต๊ะ",

    # ── ท่าทางและการโต้ตอบ (Gestures & Entertainment) ──
    "ทำท่าพยักหน้าและโบกมือทักทายแบบอีสานม่วนๆ",
    "โค้งคำนับทักทายอย่างสุภาพหน่อย",
    "ทำท่าส่ายหน้าแบบงงๆ ให้ดูหน่อย",
    "หมุนมือซ้ายขวาโชว์ท่าหน่อย",
    "เต้นฉลองโชว์สเต็ปหน่อย!",
    "เล่นเป่ายิ้งฉุบโชว์สักตาหน่อย",
    "ส่ายกล้องสำรวจรอบๆ แล้วทำท่าพยักหน้าทักทาย",
    "ขยับปลายมือหมุนซ้ายขวาพร้อมโบกมือทักทาย"
]


class RedirectText:
    def __init__(self, q):
        self.q = q
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        if "\n" in self.buffer:
            lines = self.buffer.split("\n")
            for line in lines[:-1]:
                self.q.put(line + "\n")
            self.buffer = lines[-1]

    def flush(self):
        if self.buffer:
            self.q.put(self.buffer + "\n")
            self.buffer = ""


class OneArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MyCobot 280 AI Control")
        self.root.geometry("1200x800+0+0")
        self.root.minsize(900, 600)

        Theme.apply_window_style(self.root)

        self.log_queue = queue.Queue()
        self.input_queue = queue.Queue()
        sys.stdout = RedirectText(self.log_queue)
        self.current_speaker = "sys"

        self.setup_ui()
        self.root.after(100, self.process_queue)

        # Single persistent AI worker thread
        threading.Thread(target=self._agent_loop, daemon=True).start()

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM")
        print("========================================\n")

    def setup_ui(self):
        # Set exactly 50:50 split
        self.root.columnconfigure(0, weight=1, uniform="pane")
        self.root.columnconfigure(1, weight=1, uniform="pane")
        self.root.rowconfigure(0, weight=1)

        self.left_panel = LeftPanel(parent=self.root, log_queue=self.log_queue)

        self.right_panel = RightPanel(
            parent=self.root,
            log_queue=self.log_queue,
            reset_robot_callback=self.reset_robot,
            send_message_callback=self.send_message,
        )

    def process_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if callable(msg):
                    msg()
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
        finally:
            self._handle_auto_mode()
            self.root.after(100, self.process_queue)

    def _handle_auto_mode(self):
        if hasattr(self, 'right_panel') and getattr(self.right_panel, 'auto_on', False):
            # Check if idle (input is enabled and not processing anything)
            if self.right_panel.input_entry.cget('state') == tk.NORMAL:
                if not getattr(self, '_auto_waiting', False):
                    self._auto_waiting = True
                    import random
                    # หน่วงเวลา 5-8 วินาที เพื่อให้ชัวร์ว่าหุ่นยนต์ทำภารกิจก่อนหน้าเสร็จสมบูรณ์และได้พัก
                    delay = random.randint(5000, 8000)
                    self.log_queue.put(f"⚙️ <SYSTEM>: [Auto Mode] งานเสร็จแล้ว กำลังรออีก {delay//1000} วินาทีเพื่อทำคำสั่งถัดไป...")
                    self.root.after(delay, self._trigger_auto_task)
        else:
            self._auto_waiting = False

    def _trigger_auto_task(self):
        self._auto_waiting = False
        if getattr(self.right_panel, 'auto_on', False) and self.right_panel.input_entry.cget('state') == tk.NORMAL:
            import random
            prompt = random.choice(AUTO_PROMPTS)
            
            if "{color}" in prompt:
                colors = ["แดง", "เขียว", "น้ำเงิน", "เหลือง"]
                prompt = prompt.replace("{color}", random.choice(colors))
                
            self.send_message(f"[AUTO] {prompt}")

    def _append_log(self, text):
        self.right_panel.log_text.config(state=tk.NORMAL)
        text = str(text).strip()
        if not text:
            self.right_panel.log_text.config(state=tk.DISABLED)
            return

        # Detect speaker change
        if "👨‍💻 <USER>:" in text or text.startswith("<USER>:"):
            self.current_speaker = "user"
            text = text.replace("👨‍💻 <USER>:", "👨 ").strip()
            # Add an extra newline before new speaker if not first message
            if self.right_panel.log_text.index("end-1c") != "1.0":
                self.right_panel.log_text.insert(tk.END, "\n", "sys")
        elif "🤖 <LLM>:" in text or text.startswith("<LLM>:"):
            self.current_speaker = "llm"
            text = text.replace("🤖 <LLM>:", "🤖 ").strip()
            if self.right_panel.log_text.index("end-1c") != "1.0":
                self.right_panel.log_text.insert(tk.END, "\n", "sys")
        elif (
            "<SYSTEM>:" in text
            or text.startswith("✅")
            or text.startswith("⚠️")
            or text.startswith("🔄")
            or "Image saved" in text
            or "Moving to" in text
        ):
            self.current_speaker = "sys"
            text = text.replace("<SYSTEM>:", "").strip()

        # Strip emojis (characters > 0xFFFF) to prevent Tkinter Tk_MeasureChars Segmentation Fault on Jetson!
        safe_text = "".join(c for c in text if ord(c) <= 0xFFFF)

        # Insert the text with current speaker's tag
        self.right_panel.log_text.insert(tk.END, safe_text + "\n", self.current_speaker)

        line_count = int(self.right_panel.log_text.index("end-1c").split(".")[0])
        if line_count > 1000:
            self.right_panel.log_text.delete("1.0", "500.0")

        self.right_panel.log_text.config(state=tk.DISABLED)
        self.right_panel.log_text.see(tk.END)

    def reset_robot(self):
        print("\n🔄 <SYSTEM>: กำลังรีเซ็ตหุ่นยนต์กลับสู่ตำแหน่งเริ่มต้น...")
        self.right_panel.disable_inputs(reset_text="Resetting...")
        threading.Thread(target=self._run_reset, daemon=True).start()

    def _run_reset(self):
        try:
            import time
            from hardware import init
            import armconfig

            init.mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_RESET)
            
            # Clear memory
            init.known_objects.clear()
            init.current_held_object = None
            init.current_held_coord = None
            print("🧠 <SYSTEM>: เคลียร์ความจำพิกัดของหุ่นยนต์เรียบร้อยแล้ว")
            
            time.sleep(2)
            print("✅ <SYSTEM>: รีเซ็ตเสร็จสมบูรณ์!")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: ไม่สามารถรีเซ็ตได้ - {e}")
        finally:
            self.log_queue.put(self.enable_all_inputs)

    def enable_all_inputs(self):
        self.right_panel.enable_inputs()

    def send_message(self, user_input):
        if not user_input:
            return
        self.right_panel.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        self.right_panel.disable_inputs(send_text="Processing...")
        self.input_queue.put(user_input)

    def _agent_loop(self):
        """Single persistent background thread with its own asyncio event loop."""
        from agent.agent import get_agent, process_user_input

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent = get_agent()  # keep runner agent for fallback

        while True:
            user_input = self.input_queue.get()
            try:
                speaker_on = self.right_panel.speaker_on
                loop.run_until_complete(process_user_input(user_input, agent, speaker_on=speaker_on))
            except Exception as e:
                import traceback
                print(f"\n⚠️ <ERROR>: {e}\n")
                traceback.print_exc()
            finally:
                self.log_queue.put(self.enable_all_inputs)



def start_gui():
    from hardware.init import mc, BotInit, cam_manager

    # Init robot position in background (non-blocking)
    threading.Thread(target=BotInit, args=(mc,), daemon=True).start()

    root = tk.Tk()
    app = OneArmGUI(root)

    # Start camera AFTER tkinter window is created to avoid X11/GStreamer conflict
    cam_manager.start()

    def on_closing():
        import traceback
        print("🛑 <SYSTEM>: on_closing() was called! Traceback:")
        traceback.print_stack()
        try:
            cam_manager.stop()
        except Exception:
            pass
        finally:
            try:
                # Brutally kill the resource_tracker process to prevent annoying warnings on exit
                import os, signal
                from multiprocessing.resource_tracker import _resource_tracker
                if _resource_tracker._process is not None:
                    os.kill(_resource_tracker._process.pid, signal.SIGKILL)
            except Exception:
                pass
            root.destroy()
            sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
