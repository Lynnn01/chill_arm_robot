import tkinter as tk
import customtkinter as ctk
import sys
import threading
import asyncio
import queue

from app.components.left_panel import LeftPanel
from app.components.right_panel import RightPanel
from hardware.init import cam_manager, mc
from agent.agent import get_agent, exit_function, get_contextual_input
from agents import Runner

class RedirectText:
    def __init__(self, q):
        self.q = q
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                self.q.put(line + '\n')
            self.buffer = lines[-1]

    def flush(self):
        if self.buffer:
            self.q.put(self.buffer + '\n')
            self.buffer = ""

class OneArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MyCobot 280 AI Control - Modern Edition")
        
        # Maximize window on startup
        try:
            self.root.attributes('-zoomed', True)
        except Exception:
            try:
                self.root.state('zoomed')
            except Exception:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        # Theming with CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.is_dark_mode = True
        
        self.agent = get_agent()
        self.log_queue = queue.Queue()
        self.input_queue = queue.Queue()
        sys.stdout = RedirectText(self.log_queue)
        
        self.setup_ui()
        self.root.after(100, self.process_log_queue)
        
        # Start AI worker thread
        threading.Thread(target=self.agent_worker, daemon=True).start()

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM (Modern UI)")
        print("========================================\n")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=4) # Left Panel
        self.root.columnconfigure(1, weight=5) # Right Panel
        self.root.rowconfigure(0, weight=1)

        self.left_panel = LeftPanel(
            parent=self.root, 
            log_queue=self.log_queue, 
            run_quick_action_callback=self.run_quick_action
        )
        
        self.right_panel = RightPanel(
            parent=self.root,
            log_queue=self.log_queue,
            toggle_theme_callback=self.toggle_theme,
            reset_robot_callback=self.reset_robot,
            send_message_callback=self.send_message
        )

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            ctk.set_appearance_mode("dark")
            self.right_panel.theme_btn.configure(text="☀️ Light Mode")
        else:
            ctk.set_appearance_mode("light")
            self.right_panel.theme_btn.configure(text="🌗 Dark Mode")

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if callable(msg):
                    msg()
                else:
                    self.right_panel.log_text.config(state=tk.NORMAL)
                    text = msg.strip()
                    if text:
                        if text.startswith("<USER>:"):
                            tag = "user"
                        elif text.startswith("🤖 <LLM>:"):
                            tag = "llm"
                        else:
                            tag = "sys"
                            
                        self.right_panel.log_text.insert(tk.END, text + "\n\n", tag)
                    self.right_panel.log_text.config(state=tk.DISABLED)
                    self.right_panel.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def run_quick_action(self, cmd):
        self.right_panel.input_entry.delete(0, tk.END)
        self.right_panel.input_entry.insert(0, cmd)
        self.send_message(cmd)

    def reset_robot(self):
        print("\n🔄 <SYSTEM>: กำลังรีเซ็ตหุ่นยนต์กลับสู่ตำแหน่งเริ่มต้น...")
        self.right_panel.disable_inputs()
        self.left_panel.qa_frame.config(cursor="wait")
        for b in self.left_panel.qa_btns:
            b.config(state=tk.DISABLED, bg="#666666")
        threading.Thread(target=self._run_reset, daemon=True).start()

    def _run_reset(self):
        try:
            import time
            mc.send_angles([0, 0, 0, 0, 0, -45], 50)
            time.sleep(2)
            print("✅ <SYSTEM>: รีเซ็ตเสร็จสมบูรณ์!")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: ไม่สามารถรีเซ็ตได้ - {e}")
        finally:
            self.log_queue.put(self.enable_all_inputs)

    def enable_all_inputs(self):
        self.right_panel.enable_inputs()
        for b in self.left_panel.qa_btns:
            b.config(state=tk.NORMAL, bg=self.theme["btn_bg"])

    def send_message(self, user_input):
        if not user_input:
            return
        
        self.right_panel.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        
        # Disable inputs while AI is processing
        self.right_panel.disable_inputs()
        for b in self.left_panel.qa_btns:
            b.config(state=tk.DISABLED, bg="#666666")
            
        self.input_queue.put(user_input)

    def agent_worker(self):
        # Setup loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            user_input = self.input_queue.get()
            try:
                contextual_input = get_contextual_input(user_input)
                result = loop.run_until_complete(Runner.run(self.agent, input=contextual_input))
                ai_reply = result.final_output
                print(f"\n🤖 <LLM>: {ai_reply}\n")
            except Exception as e:
                print(f"\n⚠️ <ERROR>: {e}\n")
            finally:
                self.input_queue.task_done()
                self.log_queue.put(self.enable_all_inputs)

def start_gui():
    root = ctk.CTk()
    app = OneArmGUI(root)
    
    def on_closing():
        try:
            cam_manager.stop()
            exit_function()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            sys.exit(0)
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
