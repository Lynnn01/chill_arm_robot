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
from agent import get_agent, exit_function

class RedirectText:
    """Thread-safe stdout redirection to a Tkinter Text widget"""
    def __init__(self, text_widget):
        self.output = text_widget

    def write(self, string):
        self.output.after(0, self._insert, string)

    def _insert(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)

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
        
        # Redirect standard output to the text area
        sys.stdout = RedirectText(self.log_text)

        print("========================================")
        print(" System Initialized. Welcome to ONE ARM")
        print("========================================\n")

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame (Padding around the app)
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Log area expands

        # Title Label
        title_label = tk.Label(main_frame, text="🤖 ONE ARM ASSISTANT", font=("Helvetica", 18, "bold"), 
                               bg=self.bg_color, fg=self.fg_color)
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Log Text Area 
        self.log_text = tk.Text(main_frame, wrap=tk.WORD, bg=self.bg_color, fg=self.fg_color, 
                                font=("Consolas", 11), highlightbackground=self.fg_color, 
                                highlightthickness=2, bd=0, padx=10, pady=10)
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
        self.input_entry = tk.Entry(input_frame, font=("Helvetica", 14), 
                                    bg=self.bg_color, fg=self.fg_color, insertbackground=self.fg_color,
                                    highlightbackground=self.fg_color, highlightthickness=2, bd=0)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15), ipady=8)
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        # Send Button
        self.send_button = tk.Button(input_frame, text="SEND", font=("Helvetica", 12, "bold"),
                                     bg=self.fg_color, fg=self.bg_color, activebackground="#333333", 
                                     activeforeground="white", command=self.send_message, bd=0)
        self.send_button.grid(row=0, column=1, sticky="e", ipadx=30, ipady=8)

        # Focus input automatically
        self.input_entry.focus()

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        self.input_entry.delete(0, tk.END)
        print(f"\n👨‍💻 <USER>: {user_input}")
        
        # Disable button/entry while processing
        self.send_button.config(state=tk.DISABLED, bg="#666666")
        self.input_entry.config(state=tk.DISABLED)
        
        # Run agent in background thread to prevent GUI freezing
        threading.Thread(target=self.run_agent_task, args=(user_input,), daemon=True).start()

    def run_agent_task(self, user_input):
        # Create a new event loop for this async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(Runner.run(self.agent, input=user_input))
            print(f"\n🤖 <LLM>: {result.final_output}\n")
        except Exception as e:
            print(f"\n⚠️ <ERROR>: {e}\n")
        finally:
            loop.close()
            # Re-enable inputs via main thread safely
            self.root.after(0, self.enable_inputs)

    def enable_inputs(self):
        self.send_button.config(state=tk.NORMAL, bg=self.fg_color)
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
