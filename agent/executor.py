"""
agent/executor.py — Sequential Task Executor (Zero LLM Roundtrips)

Imports the underlying raw Python functions directly (bypassing FunctionTool wrappers).
This lets us call tools immediately without going through the openai-agents async runner.
"""

import traceback
import time

def _get_raw_tool_map():
    """Import the raw (unwrapped) Python functions from each tool module."""
    import importlib, sys

    # Import each module directly and grab the raw function before @function_tool wraps it.
    # Since @function_tool replaces the name in-module, we need the wrapped object's underlying fn.
    # FunctionTool stores the original on `on_invoke_tool` but that's async + needs context.
    # Easiest: re-import modules in a fresh namespace so we can grab the originals.
    #
    # Strategy: each tool module only has one real function. We collect it by name
    # and call asyncio.run(on_invoke_tool(None, json_args)) would need context.
    # Instead we store callables that directly call the raw logic.

    from agent.tools.shares._raw import (
        raw_grab_object,
        raw_move_to,
        raw_show_object,
        raw_move,
        raw_rotate_gripper,
        raw_dance_celebrate,
        raw_gesture,
        raw_scan_object,
    )

    return {
        "grab_object":     raw_grab_object,
        "move_to":         raw_move_to,
        "show_object":     raw_show_object,
        "move":            raw_move,
        "rotate_gripper":  raw_rotate_gripper,
        "dance_celebrate": raw_dance_celebrate,
        "gesture":         raw_gesture,
        "scan_object":     raw_scan_object,
    }


def execute_plan(tasks: list, plan_summary: str = "", speaker_on: bool = True) -> list:
    """
    Execute a list of tasks sequentially without any LLM roundtrips.

    Args:
        tasks:        list of {"tool": str, "args": dict, "voice": str (optional)}
        plan_summary: Short Thai description of the overall plan
        speaker_on:   Whether to play TTS voice
    
    Returns:
        list of results for each tool
    """
    tool_map = _get_raw_tool_map()
    results = []
    last_grab_coord = None  # pass grab result forward to move_to if needed

    print(f"🤖 <SYSTEM>: เริ่มแผน — {plan_summary}")
    print(f"🤖 <SYSTEM>: มี {len(tasks)} งานที่ต้องทำ ทำต่อเนื่องเลย!")

    for i, task in enumerate(tasks):
        tool_name = task.get("tool", "")
        args = dict(task.get("args") or {})
        task_voice = task.get("voice", "")

        if tool_name not in tool_map:
            print(f"⚠️ <SYSTEM>: ไม่รู้จักคำสั่ง '{tool_name}' ข้ามไป")
            results.append({"tool": tool_name, "status": "error", "result": "Unknown tool"})
            continue
            
        # เล่นเสียงบรรยายของ task นี้ (แบบ background)
        if task_voice and speaker_on:
            import threading
            from agent.agent import _play_voice
            # ใช้ชื่อไฟล์เฉพาะสำหรับ task นี้เพื่อไม่ให้ไฟล์ล็อคตีกัน
            filename = f"speech_task_{i}.mp3"
            threading.Thread(target=_play_voice, args=(task_voice, filename), daemon=True).start()

        # Smart arg injection: move_to can use coord from previous grab
        if tool_name == "move_to" and not args.get("target_coord") and not args.get("target_name"):
            if last_grab_coord and isinstance(last_grab_coord, list):
                print(f"🤖 <SYSTEM>: move_to ใช้พิกัดจาก grab ก่อนหน้า: {last_grab_coord}")
                args["target_coord"] = last_grab_coord

        # Strip null/None args
        args = {k: v for k, v in args.items() if v is not None}

        print(f"🤖 <SYSTEM>: [{i+1}/{len(tasks)}] รัน {tool_name}({args})...")

        try:
            result = tool_map[tool_name](**args)

            # Keep grab coord for dependent move_to
            if tool_name == "grab_object" and isinstance(result, list) and len(result) >= 2:
                last_grab_coord = result

            results.append({"tool": tool_name, "status": "ok", "result": result})

        except Exception as e:
            print(f"⚠️ <SYSTEM>: {tool_name} ผิดพลาด: {e}")
            import traceback
            traceback.print_exc()
            results.append({"tool": tool_name, "status": "error", "result": str(e)})

        # หน่วงเวลา 2 วินาทีระหว่างคำสั่ง (ถ้าไม่ใช่คำสั่งสุดท้าย)
        if i < len(tasks) - 1:
            print("🤖 <SYSTEM>: รอ 2 วินาทีก่อนเริ่มคำสั่งถัดไป...")
            time.sleep(2)

    # ── Print summary ─────────────────────────────────────────────
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = len(results) - ok
    print(f"\n🤖 <SYSTEM>: ทำงานเสร็จ {ok}/{len(results)} งาน"
          + (f" (ผิดพลาด {fail} งาน)" if fail else ""))

    return results
