import tkinter as tk
import sys
import threading
import asyncio
import queue
import multiprocessing

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
        self.root.title("MyCobot 280 AI Control - Modern Flat UI")
        
        # Maximize window on startup (safe method for Jetson X11)
        self.root.geometry("1024x768+0+0")
        
        # Modern Flat Theming (Dark Mode Default)
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
        
        # Local Queue for GUI internal thread safety (closures)
        self.gui_queue = queue.Queue()
        
        # Multiprocessing Queues for AI Process Isolation
        self.mp_manager = multiprocessing.Manager()
        self.log_queue = self.mp_manager.Queue()
        self.input_queue = self.mp_manager.Queue()
        self.cmd_queue = self.mp_manager.Queue()
        self.res_queue = self.mp_manager.Queue()
        
        # Redirect stdout in main process to local GUI queue
        sys.stdout = RedirectText(self.gui_queue)
        
        self.setup_ui()
        self.root.after(100, self.process_queues)
        
        # Start Hardware RPC Server in background thread (Main Process)
        from hardware.rpc import run_rpc_server
        threading.Thread(target=run_rpc_server, args=(self.cmd_queue, self.res_queue), daemon=True).start()
        
        # Start Isolated AI Process
        from agent.worker import isolated_agent_worker
        self.ai_process = multiprocessing.Process(
            target=isolated_agent_worker,
            args=(self.input_queue, self.log_queue, self.cmd_queue, self.res_queue),
            daemon=True
        )
        self.ai_process.start()

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM")
        print("========================================\n")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=4) # Left Panel
        self.root.columnconfigure(1, weight=5) # Right Panel
        self.root.rowconfigure(0, weight=1)

        self.left_panel = LeftPanel(
            parent=self.root, 
            theme=self.theme, 
            log_queue=self.gui_queue,  # Internal GUI threads use local queue
            run_quick_action_callback=self.run_quick_action
        )
        
        self.right_panel = RightPanel(
            parent=self.root,
            theme=self.theme,
            log_queue=self.gui_queue,
            reset_robot_callback=self.reset_robot,
            send_message_callback=self.send_message
        )

    def process_queues(self):
        # Process internal GUI updates
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                if callable(msg):
                    msg()
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
            
        # Process AI Process logs
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if isinstance(msg, tuple) and msg[0] == "ENABLE_INPUTS":
                    self.enable_all_inputs()
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
            
        self.root.after(100, self.process_queues)

    def _append_log(self, text):
        self.right_panel.log_text.config(state=tk.NORMAL)
        text = text.strip()
        if text:
            if text.startswith("<USER>:"):
                tag = "user"
            elif text.startswith("🤖 <LLM>:"):
                tag = "llm"
            else:
                tag = "sys"
                
            self.right_panel.log_text.insert(tk.END, text + "\n\n", tag)
            
            # Auto-truncate log if it exceeds 1000 lines to prevent memory leaks
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
            self.gui_queue.put(self.enable_all_inputs)

    def enable_all_inputs(self):
        self.right_panel.enable_inputs()
        self.left_panel.enable_buttons()

    def send_message(self, user_input):
        if not user_input:
            return
        
        self.right_panel.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        
        # Disable inputs while AI is processing
        self.right_panel.disable_inputs()
        self.left_panel.disable_buttons()
            
        self.input_queue.put(user_input)

def start_gui():
    multiprocessing.set_start_method('spawn', force=True)
    root = tk.Tk()
    app = OneArmGUI(root)
    
    def on_closing():
        try:
            from hardware.init import cam_manager
            cam_manager.stop()
            
            if hasattr(app, 'ai_process') and app.ai_process.is_alive():
                app.ai_process.terminate()
                app.ai_process.join()
                
            from agent.agent import exit_function
            exit_function()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            sys.exit(0)
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
