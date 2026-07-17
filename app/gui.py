import tkinter as tk
import sys
import threading
import asyncio
import queue

from app.components.left_panel import LeftPanel
from app.components.right_panel import RightPanel

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
        self.root.title("MyCobot 280 AI Control")
        self.root.geometry("1024x768+0+0")
        
        self.theme = {
            "bg": "#121212", 
            "fg": "#FFFFFF", 
            "frame": "#1E1E1E", 
            "border": "#333333", 
            "btn_bg": "#3B8ED0", 
            "btn_fg": "#FFFFFF", 
            "btn_hover": "#2980B9",
            "dash_bg": "#2A2A2A",
            "danger": "#E74C3C",
            "danger_hover": "#C0392B"
        }
        self.root.configure(bg=self.theme["bg"])
        
        self.log_queue = queue.Queue()
        self.input_queue = queue.Queue()
        sys.stdout = RedirectText(self.log_queue)
        
        self.setup_ui()
        self.root.after(100, self.process_queue)
        
        # Single persistent AI worker thread
        threading.Thread(target=self._agent_loop, daemon=True).start()

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM")
        print("========================================\n")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=4)
        self.root.columnconfigure(1, weight=5)
        self.root.rowconfigure(0, weight=1)

        self.left_panel = LeftPanel(
            parent=self.root, 
            theme=self.theme, 
            log_queue=self.log_queue,
            run_quick_action_callback=self.run_quick_action
        )
        
        self.right_panel = RightPanel(
            parent=self.root,
            theme=self.theme,
            log_queue=self.log_queue,
            reset_robot_callback=self.reset_robot,
            send_message_callback=self.send_message
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
            self.root.after(100, self.process_queue)

    def _append_log(self, text):
        self.right_panel.log_text.config(state=tk.NORMAL)
        text = str(text).strip()
        if text:
            if "👨" in text or text.startswith("<USER>:"):
                tag = "user"
            elif "🤖" in text or text.startswith("<LLM>:"):
                tag = "llm"
            else:
                tag = "sys"
            self.right_panel.log_text.insert(tk.END, text + "\n\n", tag)
            
            line_count = int(self.right_panel.log_text.index('end-1c').split('.')[0])
            if line_count > 1000:
                self.right_panel.log_text.delete('1.0', '500.0')
                
        self.right_panel.log_text.config(state=tk.DISABLED)
        self.right_panel.log_text.see(tk.END)

    def run_quick_action(self, cmd):
        self.right_panel.input_entry.delete(0, tk.END)
        self.right_panel.input_entry.insert(0, cmd)
        self.send_message(cmd)

    def reset_robot(self):
        print("\n🔄 <SYSTEM>: กำลังรีเซ็ตหุ่นยนต์กลับสู่ตำแหน่งเริ่มต้น...")
        self.right_panel.disable_inputs()
        self.left_panel.disable_buttons()
        threading.Thread(target=self._run_reset, daemon=True).start()

    def _run_reset(self):
        try:
            import time
            from hardware.init import mc
            mc.send_angles([0, 0, 0, 0, 0, -45], 50)
            time.sleep(2)
            print("✅ <SYSTEM>: รีเซ็ตเสร็จสมบูรณ์!")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: ไม่สามารถรีเซ็ตได้ - {e}")
        finally:
            self.log_queue.put(self.enable_all_inputs)

    def enable_all_inputs(self):
        self.right_panel.enable_inputs()
        self.left_panel.enable_buttons()

    def send_message(self, user_input):
        if not user_input:
            return
        self.right_panel.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        self.right_panel.disable_inputs()
        self.left_panel.disable_buttons()
        self.input_queue.put(user_input)

    def _agent_loop(self):
        """Single persistent background thread with its own asyncio event loop."""
        from agent.agent import get_agent, get_contextual_input
        from agents import Runner
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent = get_agent()
        
        while True:
            user_input = self.input_queue.get()
            try:
                contextual_input = get_contextual_input(user_input)
                result = loop.run_until_complete(Runner.run(agent, input=contextual_input))
                print(f"\n🤖 <LLM>: {result.final_output}\n")
            except Exception as e:
                print(f"\n⚠️ <ERROR>: {e}\n")
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
        try:
            cam_manager.stop()
        except Exception:
            pass
        finally:
            root.destroy()
            sys.exit(0)
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
