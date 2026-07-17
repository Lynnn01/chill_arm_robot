import tkinter as tk
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
    def write(self, string):
        self.q.put(string)
    def flush(self):
        pass

class OneArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ONE ARM Command Center")
        self.root.geometry("1200x800")
        
        # Theming
        self.is_dark_mode = False
        self.colors = {
            "light": {"bg": "#FAFAFA", "fg": "#111111", "frame": "#FFFFFF", "border": "#DDDDDD", "btn_bg": "#111111", "btn_fg": "#FFFFFF", "dash_bg": "#F0F0F0"},
            "dark": {"bg": "#121212", "fg": "#E0E0E0", "frame": "#1E1E1E", "border": "#333333", "btn_bg": "#E0E0E0", "btn_fg": "#121212", "dash_bg": "#2A2A2A"}
        }
        self.theme = self.colors["light"]
        self.root.configure(bg=self.theme["bg"])
        
        self.agent = get_agent()
        self.log_queue = queue.Queue()
        sys.stdout = RedirectText(self.log_queue)
        
        self.setup_ui()
        self.root.after(100, self.process_log_queue)

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
            log_queue=self.log_queue, 
            run_quick_action_callback=self.run_quick_action
        )
        
        self.right_panel = RightPanel(
            parent=self.root,
            theme=self.theme,
            log_queue=self.log_queue,
            toggle_theme_callback=self.toggle_theme,
            reset_robot_callback=self.reset_robot,
            send_message_callback=self.send_message
        )

    def apply_theme(self):
        self.root.configure(bg=self.theme["bg"])
        
        def update_colors(widget):
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.theme["bg"])
            elif isinstance(widget, tk.LabelFrame):
                widget.configure(bg=self.theme["frame"], fg=self.theme["fg"], highlightbackground=self.theme["border"])
            elif isinstance(widget, tk.Label):
                if widget != self.left_panel.cam_label and widget not in self.left_panel.status_labels.values():
                    widget.configure(bg=self.theme["bg"], fg=self.theme["fg"])
                if widget in self.left_panel.status_labels.values():
                    widget.configure(bg=self.theme["dash_bg"], fg=self.theme["fg"])
                if widget.master == self.left_panel.dash_frame and widget not in self.left_panel.status_labels.values():
                    widget.configure(bg=self.theme["frame"], fg=self.theme["fg"])
            elif isinstance(widget, tk.Text) or isinstance(widget, tk.Entry):
                widget.configure(bg=self.theme["frame"], fg=self.theme["fg"], insertbackground=self.theme["fg"], highlightbackground=self.theme["border"], highlightcolor=self.theme["fg"])
            
            for child in widget.winfo_children():
                update_colors(child)
                
        update_colors(self.root)
        
        # Override specific buttons
        btn_config = {"bg": self.theme["btn_bg"], "fg": self.theme["btn_fg"]}
        self.right_panel.send_button.configure(**btn_config)
        self.right_panel.theme_btn.configure(**btn_config)
        for b in self.left_panel.qa_btns:
            b.configure(**btn_config)
        self.right_panel.reset_button.configure(bg="#FF3333", fg="white")
        self.right_panel.voice_btn.configure(bg="#ff9900", fg="white")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme = self.colors["dark"] if self.is_dark_mode else self.colors["light"]
        self.apply_theme()
        self.right_panel.theme_btn.config(text="☀️ Light Mode" if self.is_dark_mode else "🌗 Dark Mode")

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if callable(msg):
                    msg()
                else:
                    self.right_panel.log_text.insert(tk.END, msg)
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
        self.right_panel.disable_inputs()
        for b in self.left_panel.qa_btns:
            b.config(state=tk.DISABLED, bg="#666666")
        
        threading.Thread(target=self.run_agent_task, args=(user_input,), daemon=True).start()

    def run_agent_task(self, user_input):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            contextual_input = get_contextual_input(user_input)
            result = loop.run_until_complete(Runner.run(self.agent, input=contextual_input))
            print(f"\n🤖 <LLM>: {result.final_output}\n")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: {e}\n")
        finally:
            loop.close()
            self.log_queue.put(self.enable_all_inputs)

def start_gui():
    root = tk.Tk()
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
