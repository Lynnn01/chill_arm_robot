import tkinter as tk
from tkinter import ttk
import sys
import threading
import asyncio

# Setup environment variables before anything else
import os
from dotenv import load_dotenv
load_dotenv()
if os.getenv("LLM_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = os.getenv("LLM_BASE_URL")
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

# Import agent logic
from agents import Runner
from agent import get_agent, exit_function, get_contextual_input

import queue

class RedirectText:
    """Thread-safe stdout redirection using a Queue"""
    def __init__(self, q):
        self.q = q

    def write(self, string):
        self.q.put(string)

    def flush(self):
        pass

class OneArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ONE ARM")
        self.root.geometry("900x700")
        self.root.configure(bg="white")
        
        # Primary white, secondary black
        self.bg_color = "white"
        self.fg_color = "black"

        # Initialize the Agent
        self.agent = get_agent()
        
        # Setup the User Interface
        self.setup_ui()
        
        # Thread-safe logging queue
        self.log_queue = queue.Queue()
        sys.stdout = RedirectText(self.log_queue)
        
        # Start the queue polling loop
        self.root.after(100, self.process_log_queue)

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM")
        print("========================================\n")

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if callable(msg):
                    msg()
                else:
                    self.log_text.insert(tk.END, msg)
                    self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame (Padding around the app)
        main_frame = tk.Frame(self.root, bg=self.bg_color, bd=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Log area expands

        # Title Label
        title_frame = tk.Frame(main_frame, bg=self.bg_color)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        tk.Label(title_frame, text="ONE ARM", font=("Tahoma", 28, "bold"), bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        tk.Label(title_frame, text="INTELLIGENT ROBOTIC ASSISTANT", font=("Tahoma", 10, "bold"), bg=self.fg_color, fg=self.bg_color, padx=10, pady=5).pack(side=tk.LEFT, padx=15)

        # Log Text Area 
        self.log_text = tk.Text(main_frame, wrap=tk.WORD, bg="#FAFAFA", fg=self.fg_color, 
                                font=("Tahoma", 12), highlightbackground="#DDDDDD", highlightcolor=self.fg_color, 
                                highlightthickness=2, relief=tk.FLAT, bd=0, padx=15, pady=15)
        self.log_text.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        # Scrollbar for Text
        scrollbar = tk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=2, sticky="ns", pady=(0, 20))
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Input Area Frame
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        # Input Entry
        self.input_entry = tk.Entry(input_frame, font=("Tahoma", 14), 
                                    bg="#FAFAFA", fg=self.fg_color, insertbackground=self.fg_color,
                                    highlightbackground="#DDDDDD", highlightcolor=self.fg_color, 
                                    highlightthickness=2, relief=tk.FLAT, bd=0)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15), ipady=12)
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        # Send Button
        self.send_button = tk.Button(input_frame, text="SEND", font=("Tahoma", 12, "bold"),
                                     bg=self.fg_color, fg=self.bg_color, activebackground="#333333", 
                                     activeforeground="white", relief=tk.FLAT, bd=0, command=self.send_message)
        self.send_button.grid(row=0, column=1, sticky="e", ipadx=30, ipady=10)

        # Reset Button
        self.reset_button = tk.Button(input_frame, text="RESET", font=("Tahoma", 12, "bold"),
                                      bg="#FF3333", fg="white", activebackground="#CC0000",
                                      activeforeground="white", relief=tk.FLAT, bd=0, command=self.reset_robot)
        self.reset_button.grid(row=0, column=2, sticky="e", padx=(10, 0), ipadx=20, ipady=10)

        # Focus input automatically
        self.input_entry.focus()

    def reset_robot(self):
        print("\n🔄 <SYSTEM>: กำลังรีเซ็ตหุ่นยนต์กลับสู่ตำแหน่งเริ่มต้น...")
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.reset_button.config(state=tk.DISABLED, bg="#666666")
        threading.Thread(target=self._run_reset, daemon=True).start()

    def _run_reset(self):
        try:
            from tools import mc
            import time
            mc.send_angles([0, 0, 0, 0, 0, -45], 50)
            time.sleep(2)
            print("✅ <SYSTEM>: รีเซ็ตเสร็จสมบูรณ์!")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: ไม่สามารถรีเซ็ตได้ - {e}")
        finally:
            self.log_queue.put(self.enable_inputs)

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        self.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        
        # Disable button/entry while processing
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.reset_button.config(state=tk.DISABLED, bg="#666666")
        self.input_entry.config(state=tk.DISABLED)
        
        # Run agent in background thread to prevent GUI freezing
        threading.Thread(target=self.run_agent_task, args=(user_input,), daemon=True).start()

    def run_agent_task(self, user_input):
        # Create a new event loop for this async task
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
            self.log_queue.put(self.enable_inputs)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.fg_color)
        self.reset_button.config(state=tk.NORMAL, bg="#ff4444")
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus()

def on_closing():
    try:
        exit_function()
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = OneArmGUI(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
