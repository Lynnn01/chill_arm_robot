"""
agent/executor.py — Sequential Task Executor (Zero LLM Roundtrips)

Imports the underlying raw Python functions directly (bypassing FunctionTool wrappers).
This lets us call tools immediately without going through the openai-agents async runner.
"""

import traceback
import time


def _get_raw_tool_map():
    """Import the raw (unwrapped) Python functions from each tool module."""
    import inspect
    from agent.tools.shares import _raw as raw_module
    
    # catlazy: แมปชื่อฟังก์ชัน raw_* เป็นชื่อ tool อัตโนมัติด้วย inspect ประหยัดไป 30 บรรทัด
    mapping = {}
    for name, func in inspect.getmembers(raw_module, inspect.isfunction):
        if name.startswith("raw_"):
            tool_name = name[4:] # ตัด 'raw_' ออก
            mapping[tool_name] = func
            
    # รองรับ alias เก่าที่ชื่อไม่ตรงกันเป๊ะๆ
    mapping["play_rps"] = mapping.get("play_rps_game")
    
    return mapping


def _speak_task(task_voice: str, index: int) -> None:
    """Play this task's narration in the background (own file name so mp3 locks don't collide)."""
    import threading
    from agent.agent import _play_voice

    filename = f"speech_task_{index}.mp3"
    threading.Thread(
        target=_play_voice, args=(task_voice, filename), daemon=True
    ).start()


def _inject_grab_coord(tool_name: str, args: dict, last_grab_coord) -> None:
    """Smart arg injection: a bare move_to reuses the coord from the previous grab."""
    if (
        tool_name == "move_to"
        and not args.get("target_coord")
        and not args.get("target_name")
    ):
        if last_grab_coord and isinstance(last_grab_coord, list):
            print(
                f"🤖 <SYSTEM>: move_to ใช้พิกัดจาก grab ก่อนหน้า: {last_grab_coord}"
            )
            args["target_coord"] = last_grab_coord


def _handle_result(tool_name: str, result, last_grab_coord):
    """Returns (error_message_or_None, new_last_grab_coord)."""
    if isinstance(result, dict):
        # หากมี Error (เช่น หุ่นไปไม่ถึง, ชน, หรือ Timeout) ให้หยุดทำงานทันที!
        if result.get("status") == "ERROR":
            return result.get("message", "Unknown error"), last_grab_coord

        # หากทำงานเสร็จสมบูรณ์
        if result.get("status") == "DONE TASK" and tool_name == "grab_object":
            last_grab_coord = result.get("data")

    # รองรับกรณี tool บางตัวยัง return แบบเก่า
    elif tool_name == "grab_object" and isinstance(result, list) and len(result) >= 2:
        last_grab_coord = result
    return None, last_grab_coord


def _award_score(results: list, tasks: list, plan_summary: str) -> None:
    """Calculate and award score if all planned tasks succeeded."""
    if results and all(r.get("status") == "ok" for r in results) and len(results) == len(tasks):
        from agent import scoring
        points, reason = scoring.evaluate_task_points(tasks, plan_summary)
        scoring.add_score(points, reason)


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
        tool_name = str(task.get("tool", "")).strip().replace("()", "").rstrip("()").strip()
        args = dict(task.get("args") or {})
        # catlazy: Fallback ง่ายๆ แทนการ hardcode ดิกชันนารี 50 บรรทัด
        task_voice = task.get("voice", "") or f"กำลังทำตามคำสั่ง {tool_name} เด้อครับ"

        if tool_name not in tool_map:
            print(f"⚠️ <SYSTEM>: ไม่รู้จักคำสั่ง '{tool_name}' ข้ามไป")
            results.append(
                {"tool": tool_name, "status": "error", "result": "Unknown tool"}
            )
            continue

        # เล่นเสียงบรรยายของ task นี้ (แบบ background)
        if speaker_on:
            _speak_task(task_voice, i)

        _inject_grab_coord(tool_name, args, last_grab_coord)

        # Strip null/None args
        args = {k: v for k, v in args.items() if v is not None}

        print(f"🤖 <SYSTEM>: [{i+1}/{len(tasks)}] รัน {tool_name}({args})...")

        try:
            result = tool_map[tool_name](**args)
            err_msg, last_grab_coord = _handle_result(tool_name, result, last_grab_coord)
            if err_msg is not None:
                print(f"⚠️ <SYSTEM>: หยุดการทำงานอัตโนมัติเนื่องจาก: {err_msg}")
                results.append({"tool": tool_name, "status": "error", "result": err_msg})
                break # ขัดจังหวะ ไม่ทำคำสั่งที่เหลือต่อ!

            results.append({"tool": tool_name, "status": "ok", "result": result})

        except Exception as e:
            print(f"⚠️ <SYSTEM>: {tool_name} ผิดพลาด: {e}")
            traceback.print_exc()
            results.append({"tool": tool_name, "status": "error", "result": str(e)})
            break # ถ้าพังจากโค้ด ก็ให้หยุดทำงานเหมือนกัน

    # ── Print summary & Scoring ──────────────────────────────────
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = len(results) - ok
    print(
        f"\n🤖 <SYSTEM>: ทำงานเสร็จ {ok}/{len(results)} งาน"
        + (f" (ยกเลิกกลางคัน {fail} งาน)" if fail else "")
    )

    _award_score(results, tasks, plan_summary)
    return results
