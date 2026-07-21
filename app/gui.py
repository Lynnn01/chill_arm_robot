import tkinter as tk
import sys
import threading
import asyncio
import queue

from app.components.left_panel import LeftPanel
from app.components.right_panel import RightPanel
from app.theme import Theme


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
            self.root.after(100, self.process_queue)

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

        # Insert the text with current speaker's tag
        self.right_panel.log_text.insert(tk.END, text + "\n", self.current_speaker)

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
            from hardware.init import mc
            import armconfig

            mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_RESET)
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
        """Single persistent background thread with its own asyncio event loop.

        Two-Phase Multitask Execution:
        - Phase 1: planner.plan_tasks() → LLM returns JSON task list (1 roundtrip only)
        - Phase 2: executor.execute_plan() → runs all tasks sequentially, zero LLM roundtrips
        - Fallback: if planner returns mode=fallback, uses legacy Runner (free-form queries)
        """
        from agent.agent import get_agent, get_contextual_input, _process_and_print_result
        from agent.planner import plan_tasks, summarize_results
        from agent.executor import execute_plan
        from agents import Runner

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent = get_agent()  # keep runner agent for fallback

        while True:
            user_input = self.input_queue.get()
            try:
                contextual_input = get_contextual_input(user_input)
                speaker_on = self.right_panel.speaker_on

                # ── Phase 1: Plan ──────────────────────────────
                plan = loop.run_until_complete(plan_tasks(contextual_input))

                if plan.get("mode") == "plan":
                    # ── Phase 2: Execute (zero roundtrips) ─────
                    results = execute_plan(
                        tasks=plan.get("tasks", []),
                        plan_summary=plan.get("plan_summary", ""),
                        speaker_on=speaker_on,
                    )
                    
                    # ── Phase 3: Summarize ─────────────────────
                    print("🤖 <SYSTEM>: กำลังสรุปผลการทำงาน...")
                    final_summary = loop.run_until_complete(
                        summarize_results(contextual_input, results)
                    )
                    print("\n", end="")
                    _process_and_print_result(final_summary, speaker_on=speaker_on)
                    print("\n", end="")
                else:
                    # ── Fallback: legacy Runner ─────────────────
                    print("🤖 <SYSTEM>: ใช้ Runner ปกติ (fallback mode)...")
                    result = loop.run_until_complete(
                        Runner.run(agent, input=contextual_input)
                    )
                    print("\n", end="")
                    _process_and_print_result(result.final_output, speaker_on=speaker_on)
                    print("\n", end="")

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
        try:
            cam_manager.stop()
        except Exception:
            pass
        finally:
            root.destroy()
            sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
