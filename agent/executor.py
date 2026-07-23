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
        task_voice = task.get("voice", "")

        if tool_name not in tool_map:
            print(f"⚠️ <SYSTEM>: ไม่รู้จักคำสั่ง '{tool_name}' ข้ามไป")
            results.append(
                {"tool": tool_name, "status": "error", "result": "Unknown tool"}
            )
            continue

        if not task_voice:
            # catlazy: Fallback ง่ายๆ แทนการ hardcode ดิกชันนารี 50 บรรทัด
            task_voice = f"กำลังทำตามคำสั่ง {tool_name} เด้อครับ"

        # เล่นเสียงบรรยายของ task นี้ (แบบ background)
        if task_voice and speaker_on:
            import threading
            from agent.agent import _play_voice

            # ใช้ชื่อไฟล์เฉพาะสำหรับ task นี้เพื่อไม่ให้ไฟล์ล็อคตีกัน
            filename = f"speech_task_{i}.mp3"
            threading.Thread(
                target=_play_voice, args=(task_voice, filename), daemon=True
            ).start()

        # Smart arg injection: move_to can use coord from previous grab
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

        # --- AUTO-UNSTACK INTERCEPTOR ---
        if tool_name == "grab_object":
            from hardware import init
            from agent.tools.shares._raw import get_english_name
            import armconfig
            
            obj_name = args.get("object_name")
            if obj_name:
                eng_name = get_english_name(obj_name)
                if eng_name in init.known_objects and isinstance(init.known_objects[eng_name], list):
                    tx, ty = init.known_objects[eng_name][0:2]
                    tz = init.known_objects[eng_name][2] if len(init.known_objects[eng_name]) >= 3 else armconfig.GRAB_BASE_HEIGHT
                    
                    is_stacked = False
                    for k, v in init.known_objects.items():
                        if k == eng_name or v == "in gripper" or not isinstance(v, list) or len(v) < 2:
                            continue
                        dx = abs(v[0] - tx)
                        dy = abs(v[1] - ty)
                        vz = v[2] if len(v) >= 3 else armconfig.GRAB_BASE_HEIGHT
                        if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                            if vz > tz + 10:
                                is_stacked = True
                                break
                    if is_stacked:
                        print(f"🤖 <SYSTEM>: ระบบตรวจพบว่า '{obj_name}' โดนทับอยู่! สลับไปใช้ unstack_and_grab อัตโนมัติ")
                        tool_name = "unstack_and_grab"
        # ---------------------------------

        # Strip null/None args
        args = {k: v for k, v in args.items() if v is not None}

        print(f"🤖 <SYSTEM>: [{i+1}/{len(tasks)}] รัน {tool_name}({args})...")

        try:
            result = tool_map[tool_name](**args)
            
            if isinstance(result, dict):
                # หากมี Error (เช่น หุ่นไปไม่ถึง, ชน, หรือ Timeout) ให้หยุดทำงานทันที!
                if result.get("status") == "ERROR":
                    err_msg = result.get("message", "Unknown error")
                    print(f"⚠️ <SYSTEM>: หยุดการทำงานอัตโนมัติเนื่องจาก: {err_msg}")
                    results.append({"tool": tool_name, "status": "error", "result": err_msg})
                    break # ขัดจังหวะ ไม่ทำคำสั่งที่เหลือต่อ!
                    
                # หากทำงานเสร็จสมบูรณ์
                if result.get("status") == "DONE TASK":
                    if tool_name == "grab_object":
                        last_grab_coord = result.get("data")
                        
            # รองรับกรณี tool บางตัวยัง return แบบเก่า
            elif tool_name == "grab_object" and isinstance(result, list) and len(result) >= 2:
                last_grab_coord = result

            results.append({"tool": tool_name, "status": "ok", "result": result})

        except Exception as e:
            print(f"⚠️ <SYSTEM>: {tool_name} ผิดพลาด: {e}")
            import traceback

            traceback.print_exc()
            results.append({"tool": tool_name, "status": "error", "result": str(e)})
            break # ถ้าพังจากโค้ด ก็ให้หยุดทำงานเหมือนกัน

        # Tools จะรอจนกว่าหุ่นจะขยับเสร็จด้วยตัวเอง (wait_for_arrival / wait_for_z)
        if i < len(tasks) - 1:
            pass

    # ── Print summary ─────────────────────────────────────────────
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = len(results) - ok
    print(
        f"\n🤖 <SYSTEM>: ทำงานเสร็จ {ok}/{len(results)} งาน"
        + (f" (ยกเลิกกลางคัน {fail} งาน)" if fail else "")
    )

    return results
