"""
agent/tools/_raw.py — Raw (unwrapped) tool functions for executor.py

These are the actual Python logic functions without the @function_tool decorator,
so executor.py can call them directly without going through openai-agents async machinery.
"""

import time
import json
import math
from hardware.init import mc
from hardware import init
import armconfig

# สีของวัตถุที่รู้จัก — ใช้ตรวจ alias cleanup
_OBJECT_COLORS = frozenset({"red", "green", "blue", "yellow", "orange", "purple", "pink", "white", "black"})


# ── grab_object ──────────────────────────────────────────────────────────────────

def raw_grab_object(object_name: str, target_coord: list = None, _auto_unstack: bool = True) -> list:
    """Grab an object. Returns [x, y] robot coord."""
    from vision import eyeonhand, yolo_detector, api
    from PIL import Image
    import os

    if init.current_held_object:
        print(f"⚠️ <SYSTEM>: กริปเปอร์กำลังถือ '{init.current_held_object}' อยู่แล้ว! ป้องกันการหยิบซ้อนโดยไม่วางก่อน")
        return {"status": "ERROR", "message": f"Already holding {init.current_held_object}. Place it first with move_to."}

    init.BotInit(mc)

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    x_offset = cfg.get("x", 0)
    y_offset = cfg.get("y", 0)
    z_offset = cfg.get("z", 0)
    z = armconfig.GRAB_BASE_HEIGHT + z_offset
    eng_name = get_english_name(object_name)

    if target_coord and len(target_coord) >= 2:
        print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปหยิบของที่พิกัด {target_coord}...")
        robot_coord = [float(target_coord[0]), float(target_coord[1])]
        if len(target_coord) >= 3:
            z = float(target_coord[2]) + z_offset
    else:
        eng_name = get_english_name(object_name)
        if eng_name in init.known_objects and isinstance(init.known_objects[eng_name], list):
            saved = init.known_objects[eng_name]
            print(f"🤖 <SYSTEM>: ดึงพิกัด '{eng_name}' จากความจำ {saved} (ข้ามสแกน)...")
            robot_coord = [float(saved[0]), float(saved[1])]
            if len(saved) >= 3:
                z = float(saved[2]) + z_offset
        else:
            yolo_coord = yolo_detector.scan_with_yolo(eng_name)
            if yolo_coord:
                robot_coord = yolo_coord
                
                # SAFETY: Auto-adjust Z if camera spots it sitting on top of a known object
                max_z_at_xy = armconfig.GRAB_BASE_HEIGHT
                for k, v in init.known_objects.items():
                    if isinstance(v, list) and len(v) >= 3 and k != eng_name and "area" not in k.lower():
                        dx, dy = abs(v[0] - robot_coord[0]), abs(v[1] - robot_coord[1])
                        if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                            if v[2] > max_z_at_xy:
                                max_z_at_xy = v[2]
                                
                if max_z_at_xy > armconfig.GRAB_BASE_HEIGHT:
                    # กล้องเห็นแค่วัตถุบนสุด — ใช้ Z ของความจำตรงๆ ได้เลย
                    z = max_z_at_xy
                    print(f"🤖 <SYSTEM>: กล้องเจอวัตถุที่ซ้อนกันอยู่! ยกตัวหยิบขึ้นเป็น Z={z} ตามความจำสูงสุด")
                else:
                    print(f"🤖 <SYSTEM>: YOLO เจอแล้ว! กำลังเคลื่อนที่ไปพิกัด {robot_coord}")
                    
            else:
                print(f"🤖 <SYSTEM>: กำลังใช้กล้อง Vision AI ค้นหา '{eng_name}'...")
                init.GetImage()
                img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
                width, height = Image.open(img_path).size
                positions = api.QwenVLRequest("a " + eng_name, img_path).get("coordinates", [])
                if positions:
                    pos = positions[0]
                    cx = (pos["x1"] + pos["x2"]) / 2
                    cy = (pos["y1"] + pos["y2"]) / 2
                    pixel = (cx / 1000 * width, cy / 1000 * height)
                    np_coord = eyeonhand.pixel_to_arm(pixel)
                    robot_coord = [float(np_coord[0]) + x_offset, float(np_coord[1]) + y_offset]
                    robot_coord[0] += getattr(armconfig, 'GRAB_X_OFFSET', 0.0)
                    robot_coord[1] += getattr(armconfig, 'GRAB_Y_OFFSET', 0.0)
                    if robot_coord[0] > 210:
                        robot_coord[0] -= 5
                    print(f"🤖 <SYSTEM>: Vision เจอแล้ว! พิกัด {robot_coord}")
                else:
                    print(f"🤖 <SYSTEM>: ไม่พบ {object_name} ในภาพ")
                    return {"status": "ERROR", "message": f"ไม่พบ {object_name} ในภาพ"}

    # SAFETY: Auto-detect buried objects and unstack them!
    if _auto_unstack and not target_coord:
        tx, ty = robot_coord[0], robot_coord[1]
        for k, v in init.known_objects.items():
            if isinstance(v, list) and len(v) >= 3 and k != eng_name and "area" not in k.lower():
                dx, dy = abs(v[0] - tx), abs(v[1] - ty)
                if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                    if v[2] > z + 10:
                        print(f"⚠️ <SYSTEM>: ตรวจพบวัตถุทับอยู่บน '{eng_name}'! เปลี่ยนไปใช้กระบวนการแกะกล่อง (unstack) อัตโนมัติ...")
                        return raw_unstack_and_grab(object_name)

    # Check radius limits to prevent joint IK singularity near base
    radius = math.hypot(robot_coord[0], robot_coord[1])
    min_r = getattr(armconfig, "GRAB_MIN_RADIUS", 150.0)
    if radius < min_r and radius > 0:
        scale = min_r / radius
        robot_coord[0] *= scale
        robot_coord[1] *= scale
        print(f"🤖 <SYSTEM>: ปรับพิกัดรัศมีจาก {radius:.1f}mm เป็น {min_r}mm ป้องกันข้อต่อติดขัดใกล้ฐาน")

    robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[0]))
    robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[1]))

    init.open_gripper()
    mc.send_coords([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL], mode="coords")
    time.sleep(0.5)  # พักเคลียร์บอร์ดให้พร้อมรับคำสั่งดำดิ่งถัดไป

    print(f"🤖 <SYSTEM>: กำลังพุ่งหัวลงไปหยิบที่ Z={z}...")
    mc.send_coords([robot_coord[0], robot_coord[1], z] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    time.sleep(0.2)
    mc.send_coords([robot_coord[0], robot_coord[1], z] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)  # ส่งคำสั่งย้ำป้องกันเฟิร์มแวร์เมิน
    reached_z = mc.wait_for_z(z)   # รอเฉพาะแกน Z — ไม่สนใจ XY drift

    if not reached_z:
        print(f"⚠️ <SYSTEM>: ไม่สามารถลงไปถึงระดับหยิบ Z={z} ได้! ดึงหัวกลับตำแหน่งปลอดภัยและยกเลิกภารกิจ")
        mc.send_coords([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
        time.sleep(1.5)
        mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
        return {"status": "ERROR", "message": f"Joint stall at target Z={z}. Object unreachable."}
    
    init.close_gripper()
    time.sleep(1)  # รอกริปเปอร์หนีบเสร็จ

    eng_name = get_english_name(object_name)
    init.current_held_object = eng_name
    init.current_held_coord = [robot_coord[0], robot_coord[1]]
    init.known_objects[eng_name] = "in gripper"

    # ลบ alias เฉพาะ key ที่เป็นชื่อเดียวกันหรือ alias ของวัตถุที่เพิ่งหยิบ
    # บังคับอย่าลบวัตถุสีอื่นที่อยู่ในกองเดียวกัน
    _grabbed_color = next((c for c in _OBJECT_COLORS if c in eng_name.lower()), None)

    for k, v in list(init.known_objects.items()):
        if k == eng_name or not isinstance(v, list) or len(v) < 2:
            continue
        # ถ้า k มีชื่อสีชัดเจนและสีต่างจากที่หยิบ → ข้าม (ไม่ใช่ alias)
        _k_color = next((c for c in _OBJECT_COLORS if c in k.lower()), None)
        if _grabbed_color and _k_color and _k_color != _grabbed_color:
            continue
        dx = abs(v[0] - robot_coord[0])
        dy = abs(v[1] - robot_coord[1])
        if dx < 35.0 and dy < 35.0:
            # ตรวจว่าอยู่ชั้นเดียวกันที่ Z
            if len(v) >= 3:
                dz = abs(v[2] - z)
                if dz > 20.0:  # ต่างชั้นกันเกิน 20mm → ข้าม (คนละชิ้น)
                    continue
            init.known_objects[k] = "in gripper"


    mc.send_coords([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_DOWN, armconfig.SPEED_LIFT)
    mc.wait_for_arrival([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL], mode="coords")
    
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
        
    print(f"✅ <SYSTEM>: DONE TASK - {object_name}")

    return {"status": "DONE TASK", "data": robot_coord}


# ── move_to ──────────────────────────────────────────────────────────────────

def get_english_name(name: str) -> str:
    """Fallback translator in case LLM outputs Thai instead of English."""
    if not name: return ""
    name_lower = name.lower().strip()
    
    # Translation mapping
    translate_map = {
        "แดง": "red",
        "เขียว": "green",
        "น้ำเงิน": "blue",
        "ฟ้า": "blue",
        "เหลือง": "yellow",
        "กล่อง": "cube",
        "บล็อก": "cube",
        "พื้นที่": "area",
        "โซน": "area"
    }
    
    # Explicit exact matches for common terms
    exact_map = {
        "กล่องสีแดง": "red_cube",
        "กล่องสีเขียว": "green_cube",
        "กล่องสีน้ำเงิน": "blue_cube",
        "กล่องสีฟ้า": "blue_cube",
        "กล่องสีเหลือง": "yellow_cube",
        "พื้นที่สีแดง": "red_area",
        "พื้นที่สีเขียว": "green_area",
        "พื้นที่สีฟ้า": "blue_area",
        "พื้นที่สีน้ำเงิน": "blue_area",
        "พื้นที่สีเหลือง": "yellow_area"
    }
    
    # 1. Check exact map first
    for th, en in exact_map.items():
        if th in name_lower:
            return en
            
    # 2. Check piece-by-piece translation if no exact match
    translated = name_lower
    for th, en in translate_map.items():
        translated = translated.replace(th, en)
        
    return translated.replace(" ", "_")

def raw_move_to(target_coord: list = None, target_name: str = None, target_height: int = None) -> str:
    """Move and place current object at target_coord or on top of target_name."""
    if not init.current_held_object:
        print(f"⚠️ <SYSTEM>: กริปเปอร์ไม่ได้ถือวัตถุอยู่! ยกเลิก move_to เพื่อป้องกันแขนกลขยับเปล่า (ต้องสั่ง grab_object ก่อน)")
        return {"status": "ERROR", "message": "No object held in gripper. Call grab_object first."}

    # Check if target_coord is invalid, default [0,0], or matches the grabbed object's former location
    is_held_coord = False
    if hasattr(init, "current_held_coord") and init.current_held_coord and target_coord and isinstance(target_coord, list) and len(target_coord) >= 2:
        dx = abs(target_coord[0] - init.current_held_coord[0])
        dy = abs(target_coord[1] - init.current_held_coord[1])
        if dx < 35.0 and dy < 35.0:
            is_held_coord = True
            print(f"⚠️ <SYSTEM>: target_coord {target_coord} ตรงกับตำแหน่งเดิมของวัตถุที่ถืออยู่! ยกเลิกการใช้พิกัดซ้ำ")

    is_invalid_coord = (
        not target_coord or
        target_coord in ([0, 0], [0, 0, 0], [0.0, 0.0], [0.0, 0.0, 0.0]) or
        (isinstance(target_coord, list) and len(target_coord) >= 2 and target_coord[0] == 0 and target_coord[1] == 0) or
        is_held_coord or
        (target_name and "area" in target_name.lower())
    )

    if is_invalid_coord and target_name:
        target_coord = None
        eng_name = get_english_name(target_name)
        
        # Check matching key in init.known_objects memory (using English name)
        found_key = None
        for k, v in init.known_objects.items():
            if v != "in gripper" and isinstance(v, list) and (eng_name.lower() in k.lower() or k.lower() in eng_name.lower()):
                found_key = k
                break
        
        if found_key and isinstance(init.known_objects[found_key], list):
            target_coord = init.known_objects[found_key]
            print(f"🤖 <SYSTEM>: ใช้พิกัดของ '{found_key}' จากความจำ {target_coord}")
        else:
            from vision import yolo_detector
            print(f"🤖 <SYSTEM>: กำลังใช้กล้องสแกนหาพื้นที่ '{eng_name}' ด้วย area.pt/YOLO...")
            found_coord = yolo_detector.scan_with_yolo(eng_name)
            if found_coord:
                target_coord = found_coord
                eng_target = get_english_name(target_name)
                # พื้นที่ (area) ไม่มี Z — ใช้ -1.0 เป็น sentinel (ค่าติดลบที่เป็นไปไม่ได้ในงานจริง) เพื่อให้ dz check ทำงานได้ถูกต้อง
                init.known_objects[eng_target] = [target_coord[0], target_coord[1], -1.0]
                print(f"🤖 <SYSTEM>: สแกนพบพื้นที่ '{eng_name}' ที่พิกัด {target_coord} และจดจำพิกัดเรียบร้อยแล้ว!")
            else:
                # SAFETY STOP & HOLD OBJECT IN GRIPPER!
                print(f"⚠️ <SYSTEM>: สแกนหาพื้นที่ '{eng_name}' ไม่พบ! ยกเลิกการวางและกำกล่องไว้เพื่อความปลอดภัย")
                from agent.tts import play_voice_async
                play_voice_async(f"ข่อยสแกนหาพื้นที่ {eng_name} บ่เจอเด้อ! ยกเลิกการวางเพื่อความปลอดภัย ข่อยขอกำของไว้คือเก่าเด้อ", "area_not_found.mp3")
                mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
                mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
                return {"status": "ERROR", "message": f"ไม่พบพื้นที่ '{eng_name}' จากการสแกนด้วย area.pt! ยกเลิกการวางกล่องเพื่อความปลอดภัย (ถือกล่องไว้ในกริปเปอร์)"}

    if not target_coord or (isinstance(target_coord, list) and len(target_coord) >= 2 and target_coord[0] == 0 and target_coord[1] == 0):
        print(f"⚠️ <SYSTEM>: ไม่ทราบพิกัดเป้าหมายที่จะวาง! ยกเลิกการวางและกำกล่องไว้เพื่อความปลอดภัย")
        from agent.tts import play_voice_async
        play_voice_async("บ่รู้พิกัดพื้นที่ที่จะวางเด้อ! ยกเลิกการวางเพื่อความปลอดภัย ข่อยขอกำของไว้คือเก่าเด้อ", "no_coord.mp3")
        mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
        mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
        return {"status": "ERROR", "message": "ไม่พบพิกัดเป้าหมายที่จะวาง! ยกเลิกการวางกล่องเพื่อความปลอดภัย (ถือกล่องไว้ในกริปเปอร์)"}

    # Auto-adjust height for stacking (ถ้าไม่ได้ระบุ target_height มาจากภายนอก)
    if target_height is None:
        max_z_at_xy = None
        
        for obj_name, coord in init.known_objects.items():
            if isinstance(coord, list) and len(coord) >= 3:
                # ข้ามพื้นที่แบน ไม่นับเป็นชั้น
                if "area" in obj_name.lower() or "พื้นที่" in obj_name or "zone" in obj_name.lower():
                    continue
                    
                dx = abs(coord[0] - target_coord[0])
                dy = abs(coord[1] - target_coord[1])
                if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                    if max_z_at_xy is None or coord[2] > max_z_at_xy:
                        max_z_at_xy = coord[2]
        
        if max_z_at_xy is not None:
            # contact_point + STACK_HEIGHT_PER_LAYER = จุดสัมผัสชั้นถัดไป, บวก STACK_SAFE_OFFSET แน่นอนทุกชั้น
            target_height = max_z_at_xy + armconfig.STACK_HEIGHT_PER_LAYER + armconfig.STACK_SAFE_OFFSET
            print(f"🤖 <SYSTEM>: ตรวจพบวัตถุที่พิกัดนี้ (contact_z={max_z_at_xy}) → วางที่ Z={target_height}")
        else:
            target_height = armconfig.STACK_BASE_HEIGHT + armconfig.STACK_SAFE_OFFSET
            print(f"🤖 <SYSTEM>: ไม่พบวัตถุในบริเวณนี้ → ใช้ความสูงชั้นแรก {target_height}")


    tc = [max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[0]) + armconfig.STACK_X_OFFSET)),
          max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[1]) + armconfig.STACK_Y_OFFSET))]
    th = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, int(target_height)))

    # Dynamic approach and retreat heights based on actual target height
    # Ensures arm ALWAYS approaches from ABOVE the stack and lifts STRAIGHT UP before returning Home
    z_approach = max(armconfig.Z_PRE_PLACE, th + 40)
    z_retreat = max(armconfig.Z_SAFE_TRAVEL, th + 50)

    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่พิกัด {tc} ความสูง {th} (เข้าประชิดที่ Z={z_approach})...")
    mc.send_coords([tc[0], tc[1], z_approach] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2.5)
    mc.send_coords([tc[0], tc[1], th] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2)
    init.open_gripper()
    time.sleep(1)
    print(f"🤖 <SYSTEM>: ถอยหัวกลับแนวตั้งถึงระดับปลอดภัย Z={z_retreat} ป้องกันการสะบัดโดนของ...")
    mc.send_coords([tc[0], tc[1], z_retreat] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2)
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")

    if init.current_held_object:
        # เก็บเป็น contact_point (th - STACK_SAFE_OFFSET) เพื่อให้ชั้นถัดไปคำนวณ target_height ได้ถูกต้อง
        contact_z = th - armconfig.STACK_SAFE_OFFSET
        init.known_objects[init.current_held_object] = [round(tc[0], 2), round(tc[1], 2), round(contact_z, 2)]
        if target_name:
            eng_target = get_english_name(target_name)
            init.known_objects[eng_target] = [round(tc[0], 2), round(tc[1], 2), th - armconfig.STACK_HEIGHT_PER_LAYER]
        init.current_held_object = None

    print(f"✅ <SYSTEM>: DONE TASK - Placed at {tc}")
    return {"status": "DONE TASK", "message": "Placed successfully."}


# ── show_object ──────────────────────────────────────────────────────────────

def raw_show_object(object_name: str) -> str:
    print(f"🤖 <SYSTEM>: กำลังยก {object_name} ขึ้นแสดง...")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(1.5)
    mc.send_angles(armconfig.POSE_SHOW, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_SHOW, mode="angles")
        
    time.sleep(2.5) # โชว์ค้างไว้ 2.5 วิ
    print(f"🤖 <SYSTEM>: โชว์เสร็จเรียบร้อย ดึงหัวกลับตำแหน่งเตรียมพร้อม...")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    print(f"✅ <SYSTEM>: DONE TASK - Show {object_name}")
    return {"status": "DONE TASK"}


# ── move ─────────────────────────────────────────────────────────────────────

def raw_move(x: float, y: float, z: float, speed: int = 40) -> str:
    # Clamp X, Y, Z directly instead of using over-engineered TargetCoordinate
    x = float(x)
    y = float(y)
    z = float(z)
    
    x = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x))
    y = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y))
    z = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, z))
    
    # Apply base radius safety
    import math
    if z < 100:
        radius = math.sqrt(x**2 + y**2)
        if radius < armconfig.GRAB_MIN_RADIUS:
            if radius > 0:
                scale = armconfig.GRAB_MIN_RADIUS / radius
                x = x * scale
                y = y * scale
            else:
                x = float(armconfig.GRAB_MIN_RADIUS)
                y = 0.0

    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่ (X:{x:.1f}, Y:{y:.1f}, Z:{z:.1f}) ด้วยความเร็ว {speed}...")
    mc.send_coords([x, y, z] + armconfig.WRIST_PLACE, speed)
    mc.wait_for_arrival([x, y, z], mode="coords")
        
    print(f"✅ <SYSTEM>: DONE TASK - Moved to {x:.1f}, {y:.1f}, {z:.1f}")
    return {"status": "DONE TASK"}


# ── rotate_gripper ───────────────────────────────────────────────────────────

def raw_rotate_gripper(angle_range: int = 45, speed: int = 40) -> str:
    # Clamp angle_range to safe range (-90 to +90) to prevent Joint 6 limit overflow (-180..180)
    angle_range = max(-90, min(90, int(angle_range)))
    print(f"Rotating gripper by {angle_range} degrees...")
    current = mc.get_angles()
    j6 = current[5] if current and len(current) == 6 else -45
    
    target_pos = max(-165.0, min(165.0, j6 + angle_range))
    target_neg = max(-165.0, min(165.0, j6 - angle_range))

    mc.send_angle(6, target_pos, speed)
    time.sleep(1.2)
    mc.send_angle(6, target_neg, speed)
    time.sleep(1.5)
    mc.send_angle(6, j6, speed)
    if current and len(current) == 6:
        mc.wait_for_arrival(current, mode="angles")
        
    print(f"✅ <SYSTEM>: DONE TASK - Rotated")
    return {"status": "DONE TASK"}


# ── dance_celebrate ──────────────────────────────────────────────────────────

def raw_dance_celebrate() -> str:
    print("Dancing! 💃")
    speed = armconfig.SPEED_DANCE
    mc.send_angles([-45, 0, -20, 0, 0, -45], speed); time.sleep(1)
    mc.send_angles([45,  0, -20, 0, 0, -45], speed); time.sleep(1)
    mc.send_angles([-45, 0,  30, -30, 0, -45], speed); time.sleep(1)
    mc.send_angles([45,  0,  30, -30, 0, -45], speed); time.sleep(1)
    mc.send_angles(armconfig.POSE_HOME, speed); time.sleep(1.5)
    print(f"✅ <SYSTEM>: DONE TASK - Dance")
    return {"status": "DONE TASK"}


# ── gesture ──────────────────────────────────────────────────────────────────

def raw_gesture(action: str) -> str:
    action = action.lower()
    valid_actions = ("yes", "no", "bow", "wave", "confused")
    if action not in valid_actions:
        return f"Error: action must be one of {valid_actions}."
    print(f"Gesture: {action.upper()}")
    speed = armconfig.SPEED_DANCE
    current = mc.get_angles()
    base = current if current and len(current) == 6 else armconfig.POSE_HOME
    if action == "yes":
        j5 = base[4]
        mc.send_angle(5, j5 + 30, speed); time.sleep(0.5)
        mc.send_angle(5, j5 - 30, speed); time.sleep(0.6)
        mc.send_angle(5, j5 + 30, speed); time.sleep(0.6)
        mc.send_angle(5, j5, speed);      time.sleep(0.5)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture YES")
        return {"status": "DONE TASK"}
    elif action == "bow":
        j2, j3 = base[1], base[2]
        mc.send_angles([base[0], j2 + 20, j3 - 15, base[3], base[4], base[5]], speed); time.sleep(1.0)
        mc.send_angles(base, speed); time.sleep(1.0)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture BOW")
        return {"status": "DONE TASK"}
    elif action == "wave":
        j6 = base[5]
        mc.send_angles([base[0], base[1], base[2], -80, base[4], j6 + 45], speed); time.sleep(0.6)
        mc.send_angle(6, j6 - 45, speed); time.sleep(0.6)
        mc.send_angle(6, j6 + 45, speed); time.sleep(0.6)
        mc.send_angles(base, speed); time.sleep(0.8)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture WAVE")
        return {"status": "DONE TASK"}
    elif action == "confused":
        j5 = base[4]
        mc.send_angle(5, j5 + 35, speed); time.sleep(0.8)
        mc.send_angle(5, j5 - 35, speed); time.sleep(0.8)
        mc.send_angle(5, j5, speed);      time.sleep(0.6)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture CONFUSED")
        return {"status": "DONE TASK"}
    else:
        j1 = base[0]
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.5)
        mc.send_angle(1, j1 - 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1, speed);      time.sleep(0.5)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture NO")
        return {"status": "DONE TASK"}


# ── clean_desk ───────────────────────────────────────────────────────────────

def raw_clean_desk() -> str:
    """Scan all objects on desk and stack them neatly at corner [160, -140]."""
    print("🤖 <SYSTEM>: เริ่มภารกิจจัดโต๊ะทำงานอัตโนมัติ — กำลังมองหาวัตถุบนโต๊ะ...")
    objects_to_find = ["กล่องสีแดง", "กล่องสีเหลือง", "กล่องสีน้ำเงิน", "กล่องสีเขียว"]
    found_objects = []

    from vision import yolo_detector
    for obj in objects_to_find:
        coord = yolo_detector.scan_with_yolo(obj)
        if coord:
            found_objects.append((obj, coord))

    if not found_objects:
        print("⚠️ <SYSTEM>: ไม่พบวัตถุบนโต๊ะเลย!")
        return {"status": "DONE TASK", "message": "ไม่พบวัตถุบนโต๊ะเลย"}

    print(f"🤖 <SYSTEM>: เจอวัตถุทั้งหมด {len(found_objects)} ชิ้น! กำลังจัดเก็บเข้ามุม...")
    corner_coord = [160, -140]

    for idx, (obj_name, coord) in enumerate(found_objects):
        print(f"🤖 <SYSTEM>: [{idx+1}/{len(found_objects)}] หยิบ {obj_name} ไปจัดเก็บที่มุม...")
        res_grab = raw_grab_object(obj_name, target_coord=coord)
        if isinstance(res_grab, dict) and res_grab.get("status") == "ERROR":
            continue
        raw_move_to(target_coord=corner_coord, target_height=110)

# ── play_rps ─────────────────────────────────────────────────────────────────

def raw_play_rps_game() -> dict:
    from agent.tools.shares.rps_game import raw_play_rps_game as _play
    return _play()


# ── unstack_and_grab ─────────────────────────────────────────────────────────

def raw_unstack_and_grab(object_name: str, safe_area: str = "blank_area") -> dict:
    """Check if object is blocked by stacked items, unstack them to safe_area, then grab the target object."""
    eng_name = get_english_name(object_name)
    
    if eng_name in init.known_objects and isinstance(init.known_objects[eng_name], list):
        target_coord = init.known_objects[eng_name]
    else:
        from vision import yolo_detector
        target_coord = yolo_detector.scan_with_yolo(object_name)
        if target_coord:
            init.known_objects[eng_name] = target_coord
        else:
            return raw_grab_object(object_name)
            
    tx, ty = float(target_coord[0]), float(target_coord[1])
    tz = float(target_coord[2]) if len(target_coord) >= 3 else armconfig.GRAB_BASE_HEIGHT
    
    blocking_objects = []
    for k, v in init.known_objects.items():
        if k == eng_name or v == "in gripper" or not isinstance(v, list) or len(v) < 2:
            continue
            
        dx = abs(v[0] - tx)
        dy = abs(v[1] - ty)
        vz = v[2] if len(v) >= 3 else armconfig.GRAB_BASE_HEIGHT
        
        if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
            if vz > tz + 10:
                blocking_objects.append((k, vz))
                
    blocking_objects.sort(key=lambda x: x[1], reverse=True)
    
    if blocking_objects:
        print(f"🤖 <SYSTEM>: ตรวจพบวัตถุทับอยู่บน '{object_name}' จำนวน {len(blocking_objects)} ชิ้น! เริ่มกระบวนการแกะออก...")
        for b_name, b_z in blocking_objects:
            print(f"🤖 <SYSTEM>: [Unstack] กำลังหยิบ '{b_name}' ออกไปวางที่พื้นที่ปลอดภัย...")
            res_grab = raw_grab_object(b_name)
            if isinstance(res_grab, dict) and res_grab.get("status") == "ERROR":
                print(f"⚠️ <SYSTEM>: ล้มเหลวขณะพยายามหยิบ '{b_name}' ออก")
                return res_grab
            
            # ใช้พิกัดจริงแทน target_name ลอยๆ เพื่อให้หุ่นเอาไปวางได้สำเร็จ
            safe_coord = [armconfig.UNSTACK_SAFE_X, armconfig.UNSTACK_SAFE_Y]
            res_move = raw_move_to(target_coord=safe_coord)  # target_height=None → auto-adjust
            if isinstance(res_move, dict) and res_move.get("status") == "ERROR":
                print(f"⚠️ <SYSTEM>: ล้มเหลวขณะพยายามวาง '{b_name}' ลงพื้นที่ปลอดภัย")
                return res_move
    else:
        print(f"🤖 <SYSTEM>: ไม่มีวัตถุทับอยู่บน '{object_name}' สามารถหยิบได้ทันที")
        
    print(f"🤖 <SYSTEM>: พื้นที่เปิดทางแล้ว! กำลังหยิบเป้าหมายหลัก '{object_name}'...")
    return raw_grab_object(object_name)


# ── scan_object ──────────────────────────────────────────────────────────────

def raw_scan_object(object_name: str) -> str:
    from vision import yolo_detector
    yolo_coord = yolo_detector.scan_with_yolo(object_name)
    if yolo_coord:
        eng_name = get_english_name(object_name)
        init.known_objects[eng_name] = yolo_coord
        print(f"✅ <SYSTEM>: DONE TASK - Scan {object_name}")
        return {"status": "DONE TASK", "message": f"Found '{object_name}' at {yolo_coord}. Memory updated."}
    return {"status": "ERROR", "message": f"'{object_name}' not found."}
