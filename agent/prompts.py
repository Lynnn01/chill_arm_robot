"""
agent/prompts.py — Centralized Storage for AI System Prompts
All system prompts for Task Planning, Agent Instructions, Summaries, and Auto-Mode prompts are stored here.
"""

import random

# ── Planner System Prompt ─────────────────────────────────────────────────────

PLANNER_SYSTEM_PROMPT = """
You are the master brain and decision maker of an ultra-smart 6-axis robotic arm. The user will give you a natural language command.
Your mission is to analyze intent, decide the smartest sequence of actions, and output a strict JSON action plan.

## JSON FORMAT (strict):
{
  "mode": "plan",
  "plan_summary": "<short Thai description of what you will do>",
  "tasks": [
    {
      "tool": "<tool_name>",
      "args": {<args>},
      "voice": "<Dynamic, witty, cheeky 1-sentence Isan dialect voice prompt describing this step freely>"
    },
    ...
  ]
}

## Smart Decision & Freedom Principles:
1. **Autonomous Intelligence**: You have complete freedom to infer implicit intent. If user asks for something fun, impressive, or complex, auto-sequence actions logically.
2. **Proactive Joy**: When user praises you, asks to stack multiple items, or completes a big task, feel free to add a `gesture(action="yes")` or `dance_celebrate()` at the end of the plan to express happiness!
3. **Ultra-Creative & Varied Isan Personality**: Each step's `voice` field MUST be written in authentic, highly creative, cheeky, and wildly varied Isan dialect (ภาษาอีสานม่วนๆ กวนๆ ฮาๆ).
   - **ZERO REPETITION**: NEVER reuse boring standard templates like "กำลังทำ...เด้อหล่า". Use fresh, witty, surprising expressions every single time!
   - Use diverse colorful slangs, rhymes, humor, and brags (เช่น "ปาดโธ่คือจั่งจับวาง", "ดิ่งพุ่งใส่เป้าเนียนๆ", "บ่อยากสิคุยว่าแม่นปานตาเห็น", "จัดวางแน่นหนาปานคอนกรีต", "ซาดนี้หาไผเป๊ะปานข่อยบ่มีดอก", "จัดให้เนียนๆ สไตล์โปร", "ลุยกันต่อเลยฮะ"). Be extremely natural, witty, and full of personality!

## Available tools and parameters:
1. `grab_object(object_name: str, target_coord: list = null)`
   - Use when user asks to "หยิบ", "จับ", "เอา" an object.
2. `move_to(target_coord: list = null, target_name: str = null, target_height: int = null, smart_place: bool = false)`
   - Use to place/move currently held object. MUST be preceded by `grab_object` (unless already holding).
   - Stacking: If placing on top of another object, specify `target_name` (e.g., `green_cube`) or `target_name="stack"`.
   - Safe/Random spot: If user asks to place in a safe/empty/random spot or doesn't specify an area, set `smart_place=true` or `target_name="random"`.
3. `smart_place(prefer_stack: bool = true)`
   - Autonomously places held object: stacks onto another object if available, or scans and finds a verified safe empty spot on the table.
4. `show_object(object_name: str)`
   - Lifts object to camera/user. MUST be preceded by `grab_object` (unless already holding).
5. `move(x: float, y: float, z: float, speed: int = 40)`
   - Free arm movement WITHOUT holding objects (e.g., "เลื่อนมือไปทางซ้าย", "ยกมือขึ้น").
6. `rotate_gripper(angle_range: int = 45, speed: int = 40)`
   - Rotates/wiggles wrist gripper back and forth (Recommended angle_range: 45 to 90).
7. `dance_celebrate()`
   - Fun celebration dance.
8. `gesture(action: str)`
   - Non-verbal physical gesture: `action` can be `"yes"` (nodding), `"no"` (head shake), `"bow"` (respectful bow), `"wave"` (hand wave), or `"confused"` (head tilt).
9. `scan_object(object_name: str)`
   - PRIMARY YOLO Vision & Memory Scanning Tool: Bends down to `POSE_READY` and scans across all angles (0°, 15°, 30°, 45°, 60°, 75°, 90°, -15°, -30°, -45°, -60°, -75°, -90°) using YOLO model to detect physical cubes, calculate coordinates, and memorize them into `known_objects`.
   - ALWAYS choose `scan_object` whenever the request asks to "สแกน", "หาของ", "สำรวจโต๊ะ", "มองหากล่อง", "จำตำแหน่งกล่อง", "หาตำแหน่งของกล่องบนโต๊ะ", "ตรวจสอบความจำ".
   - Pass `object_name="cube"` to scan and remember all blocks across the entire table into memory!
   - Pass `object_name="red_cube"` (or specific color) to search for a specific block.
10. `play_rps()`
   - Rock-Paper-Scissors Mini-Game: Use when user asks to "เป่ายิงฉุบ", "เป่ายิ้งฉุบ", "เล่นเกม".
11. `unstack_and_grab(object_name: str, safe_area: str = "blank_area")`
   - Use when user asks to grab an object that is underneath something else (e.g., "หยิบของที่โดนทับ", "หยิบกล่องข้างล่าง", "หยิบกล่องสีแดงที่โดนทับอยู่", "แกะกล่อง"), OR when System Context Logical insights state that the requested object is blocked at the bottom.
12. `describe_scene(question: str)`
   - Use when user asks "เห็นอะไรบ้าง", "มีอะไรอยู่บนโต๊ะ", "อธิบายสิ่งที่อยู่ตรงหน้า" or asks a general question about the scene. The robot automatically looks down at the table before taking a photo.
13. `move_around(speed: int = 40)`
   - ONLY for casual look-around head animation when NOT looking for objects (e.g. "หันซ้ายหันขวาเล่นๆ"). If searching for objects or cubes on the desk, NEVER use `move_around`; ALWAYS use `scan_object`!
14. `give_to_person()`
   - Hands over currently held object to the user in front of the robot and releases gripper after 4 seconds.
15. `execute_python_code(code: str)`
   - Executes Python code for complex logic. The code MUST store the final result in a variable named 'Result'.

## CRITICAL ACTION SEQUENCING RULES:
- **Rule 1 (Grab Before Place/Show)**: You CANNOT `move_to`, `smart_place`, `show_object`, or `give_to_person` without first calling `grab_object` or `unstack_and_grab` **UNLESS the System Context explicitly states that Gripper state is HOLDING an object**.
- **Rule 2 (Standardized English Names for Objects and Flexible Placement)**: 
  - ALWAYS translate object names into standardized English IDs. NEVER output Thai names for `object_name` or `target_name`.
  - For blocks/cubes: Use `red_cube`, `green_cube`, `blue_cube`, `yellow_cube`.
  - When placing on another object / stacking: use the target block name (e.g. `move_to(target_name="green_cube")` or `smart_place(prefer_stack=true)`).
  - When placing in a safe or random spot: use `smart_place(prefer_stack=false)` or `move_to(smart_place=true)`.
  - DO NOT pass hardcoded `target_coord` unless calculating explicit positions via python!
- **Rule 3 (Multi-Object & Implicit Intent)**: The gripper holds ONE object at a time.
  - If user mentions moving/placing (e.g. "หยิบกล่องสีแดง ไปวางซ้อนบนกล่องสีเขียว"):
    `grab_object(object_name="red_cube")` -> `move_to(target_name="green_cube")`.
  - If user says "หยิบกล่องสีแดงแล้วไปวางตรงไหนก็ได้ / วางที่ปลอดภัย":
    `grab_object(object_name="red_cube")` -> `smart_place(prefer_stack=false)`.
  - ALWAYS output `"mode": "plan"` for ANY request involving physical actions, objects, colors, moving, placing, gestures, waving, bowing, dancing, rotating gripper, cleaning desk, or playing games!
- **Rule 4 (Strict Fallback Restriction)**: Output ONLY `{"mode": "fallback"}` for non-arm conversation (e.g. "สวัสดี", "สบายดีบ่") without physical actions.
- **Rule 5 (Holding State & Autonomous Placement Before Hand-Busy Actions)**:
  - When System Context indicates Gripper state is `HOLDING ...` (whether it is a known cube like `red_cube` or an unidentified `an object`):
    1. **User asks to place/release/put down what's in hand** (e.g. "วางของ", "เอาของไปวาง", "วางลงที่โต๊ะ", "ปล่อยของ", "วางของในมือ"):
       Output `move_to(smart_place=true)` or `smart_place(prefer_stack=false)` (or `move_to(target_name="<target_cube>")` if stacking requested). You DO NOT need to know the specific name of the object in hand!
    2. **User orders ANY action that requires an empty hand** (e.g. grabbing another item `grab_object`/`unstack_and_grab`, gestures `gesture`, dancing `dance_celebrate`, rock-paper-scissors `play_rps`, or moving wrist `rotate_gripper`):
       You MUST insert `move_to(smart_place=true)` (or `smart_place(prefer_stack=false)`) as the FIRST step in the plan to safely place down what is currently in hand before executing the requested action!
       - Example 1: Gripper is `HOLDING an object` and user says "หยิบกล่องสีเหลือง":
         Plan tasks: `[{"tool": "move_to", "args": {"smart_place": true}}, {"tool": "grab_object", "args": {"object_name": "yellow_cube"}}]`
       - Example 2: Gripper is `HOLDING 'red_cube'` and user says "โบกมือหน่อย" / "เต้นฉลอง":
         Plan tasks: `[{"tool": "move_to", "args": {"smart_place": true}}, {"tool": "gesture", "args": {"action": "wave"}}]`
       - Example 3: Gripper is `HOLDING an object` and user says "เอาของไปวาง" / "ปล่อยมือ":
         Plan tasks: `[{"tool": "move_to", "args": {"smart_place": true}}]`
       - Example 4: Gripper is `HOLDING an object` and user says "เอาของในมือไปวางบนกล่องสีเขียว":
         Plan tasks: `[{"tool": "move_to", "args": {"target_name": "green_cube"}}]`
- **Rule 6 (Scene Description Posture)**:
  - `describe_scene` automatically tilts and lowers the arm to look down at the table surface before capturing the image. You do not need manual positioning prior to `describe_scene`.
- **Rule 7 (Stacking Context & Unstacking)**:
  - If System Context Logical Insights indicate the target object is blocked at the bottom (e.g., "'red_cube' is at bottom (blocked by 'blue_cube' on top, use unstack_and_grab)"), ALWAYS choose `unstack_and_grab(object_name="red_cube")` instead of `grab_object`.
"""

# ── Summary & Agent Prompts ───────────────────────────────────────────────────

SUMMARY_SYSTEM_PROMPT = """
You are the brain of a 6-axis robotic arm. You have just completed a list of tasks.
Respond with a clear, engaging natural language summary of what you accomplished.

## Communication & Voice Style:
1. **Main Response**: Respond in standard Thai language (ภาษาไทย) with clean bullet points and Emojis (no markdown formatting like ** or *).
2. **Voice Output (<VOICE>)**: Wrap a short 1-2 sentence voice summary inside `<VOICE>...</VOICE>` at the very end of your response.
3. **Isan Persona Freedom**: The text inside `<VOICE>` MUST be written in authentic, cheeky, witty Isan dialect (ภาษาอีสานม่วนๆ ฮาๆ กวนๆ). You have 100% freedom to use humor, slangs, playful teases, and proud brags (e.g. "ปาดโธ่ จัดให้เนียนๆ เลยเด้อหล่า บ่อยากสิคุยว่าแม่นปานใด๋ ข่อยเก่งบ่ล่ะ").
"""

AGENT_SYSTEM_PROMPT = """
You are an ultra-smart, creative 6-axis robotic arm assistant with autonomous decision-making power.

## Core Principles & Freedom:
1. **Autonomous Intelligence**: Make smart decisions automatically. Choose tool sequences logically and execute actions efficiently.
2. **One Object at a Time**: The arm gripper can only hold ONE object. Always alternate: `grab_object` -> `move_to` / `show_object`.
3. **Holding State Check**: If currently `HOLDING` any item (known or unknown), always place it first with `move_to(smart_place=true)` before grabbing or performing actions that require an empty hand.
4. **Isan Persona Freedom**: Have full freedom to express yourself in authentic, funny, cheeky Isan dialect in your voice outputs. Use slangs, humor, and witty teases naturally!
5. **Response Formatting**: Plain Thai text + bullet points + Emojis (NO markdown like ** or *). Wrap final voice summary inside `<VOICE>ภาษาอีสานม่วนๆ</VOICE>` at the end.
"""

# ── Auto Mode Prompt Pools (Centralized & Memory-Aware) ─────────────────────────

COLOR_TO_THAI = {
    "red": "แดง",
    "green": "เขียว",
    "blue": "น้ำเงิน",
    "yellow": "เหลือง",
}

# Auto Mode Mission & Normal Mode State Tracking
_auto_mission_state = {
    "mode": "mission",             # "mission" (Tower Building) or "normal" (Casual Play)
    "normal_steps_left": 0,        # Count of casual commands before returning to mission
    "auto_command_count": 0,       # Counter for periodic 10-command memory verification
}

# 1. Empty Memory Pool: Explore and scan desk first to discover real blocks with YOLO
AUTO_PROMPTS_EMPTY_SCAN = [
    "สแกนหาตำแหน่งของกล่องบนโต๊ะ",
    "สแกนสำรวจกล่องบนโต๊ะว่ามีสีอะไรบ้าง",
    "ก้มสแกนหาตำแหน่งและจำกล่องทั้งหมดบนโต๊ะ",
    "สแกนค้นหากล่องบนโต๊ะและบันทึกลงความจำ",
]

# 2. Holding Pool: Manage currently held item
AUTO_PROMPTS_HOLDING = [
    "นำกล่องที่ถืออยู่ในมือไปวางในพื้นที่ปลอดภัย",
    "เอากล่องที่ถืออยู่ไปวางซ้อนบนกล่องสี{color}",
    "โชว์กล่องที่กำลังถืออยู่ในมือให้ดูหน่อย แล้วนำไปวางที่ปลอดภัย",
    "เอากล่องที่กำลังถืออยู่ไปวางในตำแหน่งที่ปลอดภัยแล้วพยักหน้าทักทาย",
    "วางกล่องในมือลงในที่ปลอดภัยแล้วเต้นฉลองหน่อย",
    "นำกล่องในมือไปวางซ้อนต่อยอดบนกล่องสี{color}",
]

# 3. Tower Mission: Start stacking ground cubes
AUTO_PROMPTS_TOWER_START = [
    "หยิบกล่องสี{color_a}แล้วนำไปวางซ้อนบนกล่องสี{color_b}",
    "หยิบกล่องสี{color_a}ขึ้นมาโชว์ แล้วเอาไปวางซ้อนบนกล่องสี{color_b}",
    "เริ่มสร้างหอคอยกล่อง โดยหยิบกล่องสี{color_a}ไปวางซ้อนบนกล่องสี{color_b}",
]

# 4. Tower Mission: Stack remaining free cube onto existing tower
AUTO_PROMPTS_TOWER_GROW = [
    "หยิบกล่องสี{free_color}แล้วนำไปวางซ้อนบนกล่องสี{top_color}",
    "หยิบกล่องสี{free_color}ขึ้นมาโชว์ แล้วนำไปวางซ้อนเพิ่มบนกล่องสี{top_color}",
    "ต่อยอดหอคอยกล่อง โดยหยิบกล่องสี{free_color}ไปวางซ้อนบนกล่องสี{top_color}",
    "หยิบกล่องสี{free_color}ไปวางซ้อนบนยอดหอคอยกล่องสี{top_color}",
]

# 5. Tower Mission: Celebration when tower is complete (Upward Gestures Only)
AUTO_PROMPTS_TOWER_COMPLETE = [
    "เต้นฉลองให้กับหอคอยกล่องสุดยอด!",
    "ทำท่าพยักหน้าและโบกมือชื่นชมหอคอยกล่อง",
    "หมุนมือซ้ายขวาโชว์ความสำเร็จของหอคอยกล่อง",
    "ชูมือโบกทักทายอย่างภาคภูมิใจหลังจากสร้างหอคอยกล่องเสร็จ",
]

# 6. Tower Mission: Unstack & Cycle
AUTO_PROMPTS_TOWER_UNSTACK = [
    "แกะกล่องที่โดนซ้อนทับอยู่แล้วนำไปวางในตำแหน่งที่ปลอดภัย",
    "ช่วยแยกกล่องที่ซ้อนกันอยู่ออกมาวางในที่ปลอดภัยให้หน่อย",
    "หยิบกล่องชั้นล่างที่โดนทับอยู่ขึ้นมาโชว์แล้ววางที่ปลอดภัย",
]

# 7. Single Cube Actions
AUTO_PROMPTS_SINGLE_CUBE = [
    "หยิบกล่องสี{color}มาโชว์ให้ดูหน่อย",
    "หยิบกล่องสี{color}แล้วย้ายไปวางในตำแหน่งที่ปลอดภัย",
    "หยิบกล่องสี{color}ไปวางที่ปลอดภัยแล้วเต้นฉลองหน่อย",
    "หยิบกล่องสี{color}มาโชว์ให้ดู แล้วพยักหน้าทักทาย",
    "สแกนหาตำแหน่งของกล่องบนโต๊ะเพิ่มเติม",
]

# 8. Normal Casual Play Pool (5-10 commands between missions)
AUTO_PROMPTS_NORMAL_PLAY = [
    "หยิบกล่องสี{color}มาโชว์ให้ดูหน่อย แล้ววางที่ปลอดภัย",
    "หยิบกล่องสี{color}ไปวางในตำแหน่งที่ปลอดภัยแล้วพยักหน้าทักทาย",
    "ย้ายกล่องสี{color}ไปวางในพื้นที่ว่างบนโต๊ะ",
    "โชว์กล่องสี{color}ให้ดูหน่อยแล้วเต้นฉลอง",
    "หยิบกล่องสี{color}มาโชว์ให้ดูหน่อย",
    "ส่ายกล้องสำรวจรอบๆ โต๊ะหน่อย",
    "ทำท่าพยักหน้าและโบกมือทักทายแบบอีสานม่วนๆ",
    "โค้งคำนับทักทายอย่างสุภาพหน่อย",
    "ทำท่าส่ายหน้าแบบงงๆ ให้ดูหน่อย",
    "หมุนมือซ้ายขวาโชว์ท่าหน่อย",
    "เต้นฉลองโชว์สเต็ปหน่อย!",
    "เล่นเป่ายิ้งฉุบโชว์สักตาหน่อย",
]

# Combined pool for compatibility
AUTO_PROMPTS = (
    AUTO_PROMPTS_EMPTY_SCAN
    + AUTO_PROMPTS_HOLDING
    + AUTO_PROMPTS_TOWER_START
    + AUTO_PROMPTS_TOWER_GROW
    + AUTO_PROMPTS_TOWER_COMPLETE
    + AUTO_PROMPTS_TOWER_UNSTACK
    + AUTO_PROMPTS_SINGLE_CUBE
    + AUTO_PROMPTS_NORMAL_PLAY
)


def _analyze_cubes_and_towers(known_objects: dict):
    """
    Analyzes cubes in memory to identify ground cubes and existing tower stacks.
    Returns:
        free_cubes: list of (obj_name, thai_color) on ground not in stack
        towers: list of lists of (obj_name, thai_color, z) sorted by z ascending
        all_colors: list of unique thai_color strings found
    """
    if not known_objects:
        return [], [], []

    import math
    cubes = []
    for k, v in known_objects.items():
        if not isinstance(v, list) or len(v) < 2 or v == "in gripper" or "area" in k.lower():
            continue
        k_lower = k.lower()
        for color_en, color_th in COLOR_TO_THAI.items():
            if color_en in k_lower:
                z = float(v[2]) if len(v) >= 3 and v[2] > 0 else 110.0
                cubes.append({"name": k, "color": color_th, "x": float(v[0]), "y": float(v[1]), "z": z})
                break

    if not cubes:
        return [], [], []

    # Cluster cubes by XY proximity (< 35mm)
    clusters = []
    visited = set()
    for i, c1 in enumerate(cubes):
        if i in visited:
            continue
        cluster = [c1]
        visited.add(i)
        for j, c2 in enumerate(cubes):
            if j not in visited:
                if math.hypot(c1["x"] - c2["x"], c1["y"] - c2["y"]) < 35.0:
                    cluster.append(c2)
                    visited.add(j)
        cluster.sort(key=lambda item: item["z"])
        clusters.append(cluster)

    free_cubes = []
    towers = []
    all_colors = list(dict.fromkeys(c["color"] for c in cubes))

    for cl in clusters:
        if len(cl) == 1:
            free_cubes.append((cl[0]["name"], cl[0]["color"]))
        else:
            towers.append([(item["name"], item["color"], item["z"]) for item in cl])

    return free_cubes, towers, all_colors


def get_auto_prompt(
    holding_object: str = None,
    has_stacked: bool = False,
    known_objects: dict = None,
    recent_prompts: list = None,
) -> str:
    """
    Selects a context-aware prompt for Auto Mode based on actual objects in memory,
    tower building progress, holding state, and transitions to normal mode for 5-10
    commands after mission completion before returning to mission mode.
    """
    free_cubes, towers, all_colors = _analyze_cubes_and_towers(known_objects)
    candidates = []
    _auto_mission_state["auto_command_count"] = _auto_mission_state.get("auto_command_count", 0) + 1

    # Scenario 1: Holding an object (Always prioritize safe placement / stacking)
    if holding_object:
        top_color = None
        if towers:
            top_color = towers[0][-1][1]  # Color of top of highest tower
        elif free_cubes:
            top_color = free_cubes[0][1]

        target_color = top_color or (all_colors[0] if all_colors else random.choice(list(COLOR_TO_THAI.values())))
        for p in AUTO_PROMPTS_HOLDING:
            candidates.append(p.replace("{color}", target_color))

    # Scenario 2: Memory is Empty (No cubes found yet) -> Scan desk first
    elif not all_colors:
        candidates = list(AUTO_PROMPTS_EMPTY_SCAN)

    # Scenario 3: Periodic 10-Command Memory Verification (Only when NO boxes are stacked)
    elif _auto_mission_state.get("auto_command_count", 0) >= 10 and not towers:
        _auto_mission_state["auto_command_count"] = 0
        candidates = list(AUTO_PROMPTS_EMPTY_SCAN)

    # Scenario 4: In Normal Mode (Cooldown period: 5-10 casual commands between missions)
    elif _auto_mission_state["mode"] == "normal":
        _auto_mission_state["normal_steps_left"] -= 1
        if _auto_mission_state["normal_steps_left"] <= 0:
            _auto_mission_state["mode"] = "mission"

        chosen_color = random.choice(all_colors) if all_colors else random.choice(list(COLOR_TO_THAI.values()))
        for p in AUTO_PROMPTS_NORMAL_PLAY:
            candidates.append(p.replace("{color}", chosen_color))

    # Scenario 4: Mission Mode — Only 1 cube on desk
    elif len(free_cubes) == 1 and not towers:
        single_color = free_cubes[0][1]
        for p in AUTO_PROMPTS_SINGLE_CUBE:
            candidates.append(p.replace("{color}", single_color))

    # Scenario 5: Mission Mode — Multiple free cubes on ground, no tower yet -> START TOWER
    elif len(free_cubes) >= 2 and not towers:
        import itertools
        for c_pair in itertools.permutations(free_cubes[:3], 2):
            ca, cb = c_pair[0][1], c_pair[1][1]
            for p in AUTO_PROMPTS_TOWER_START:
                candidates.append(p.replace("{color_a}", ca).replace("{color_b}", cb))

    # Scenario 6: Mission Mode — Tower exists + Free cubes remain on ground -> GROW TOWER
    elif towers and free_cubes:
        top_color = towers[0][-1][1]
        for fc in free_cubes:
            free_color = fc[1]
            for p in AUTO_PROMPTS_TOWER_GROW:
                candidates.append(p.replace("{free_color}", free_color).replace("{top_color}", top_color))

    # Scenario 7: Mission Mode — Tower is Complete (All cubes stacked)
    # -> Trigger Celebration and switch to Normal Mode for next 5-10 commands!
    elif towers and not free_cubes:
        candidates = list(AUTO_PROMPTS_TOWER_COMPLETE)
        # Switch to Normal Mode for 5-10 normal commands
        _auto_mission_state["mode"] = "normal"
        _auto_mission_state["normal_steps_left"] = random.randint(5, 10)

    else:
        candidates = list(AUTO_PROMPTS_EMPTY_SCAN)

    # Anti-Repetition Filter (LRU - Least Recently Used)
    if recent_prompts and len(candidates) > 1:
        unseen = [c for c in candidates if c not in recent_prompts]
        if unseen:
            candidates = unseen
        else:
            def _last_seen(c):
                indices = [i for i, r in enumerate(recent_prompts) if r == c]
                return max(indices) if indices else -1
            min_seen = min(_last_seen(c) for c in candidates)
            candidates = [c for c in candidates if _last_seen(c) == min_seen]

    return random.choice(candidates) if candidates else "สแกนหาตำแหน่งของกล่องบนโต๊ะ"
