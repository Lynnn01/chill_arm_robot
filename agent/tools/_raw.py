"""
agent/tools/_raw.py — Raw (unwrapped) tool functions for executor.py

These are the actual Python logic functions without the @function_tool decorator,
so executor.py can call them directly without going through openai-agents async machinery.
"""

import time
import json
from hardware.init import mc
from hardware import init


# ── grab_object ──────────────────────────────────────────────────────────────

def raw_grab_object(object_name: str, target_coord: list = None) -> list:
    """Grab an object. Returns [x, y] robot coord."""
    from vision import eyeonhand, yolo_detector, api
    from PIL import Image
    import os

    init.BotInit(mc)

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    x_offset = cfg.get("x", 0)
    y_offset = cfg.get("y", 0)
    z_offset = cfg.get("z", 0)
    z = 120 + z_offset

    if target_coord and len(target_coord) >= 2:
        print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปหยิบของที่พิกัด {target_coord}...")
        robot_coord = [float(target_coord[0]), float(target_coord[1])]
    elif object_name in init.known_objects and isinstance(init.known_objects[object_name], list):
        saved = init.known_objects[object_name]
        print(f"🤖 <SYSTEM>: ดึงพิกัด '{object_name}' จากความจำ {saved} (ข้ามสแกน)...")
        robot_coord = [float(saved[0]), float(saved[1])]
    else:
        yolo_coord = yolo_detector.scan_with_yolo(object_name)
        if yolo_coord:
            robot_coord = yolo_coord
            print(f"🤖 <SYSTEM>: YOLO เจอแล้ว! กำลังเคลื่อนที่ไปพิกัด {robot_coord}")
        else:
            print(f"🤖 <SYSTEM>: กำลังใช้กล้อง Vision AI ค้นหา '{object_name}'...")
            init.GetImage()
            img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
            width, height = Image.open(img_path).size
            positions = api.QwenVLRequest("a " + object_name, img_path).get("coordinates", [])
            if positions:
                pos = positions[0]
                cx = (pos["x1"] + pos["x2"]) / 2
                cy = (pos["y1"] + pos["y2"]) / 2
                pixel = (cx / 1000 * width, cy / 1000 * height)
                np_coord = eyeonhand.pixel_to_arm(pixel)
                robot_coord = [float(np_coord[0]) + x_offset, float(np_coord[1]) + y_offset]
                if robot_coord[0] > 210:
                    robot_coord[0] -= 5
                print(f"🤖 <SYSTEM>: Vision เจอแล้ว! พิกัด {robot_coord}")
            else:
                print(f"🤖 <SYSTEM>: ไม่พบ {object_name} ในภาพ")
                return []

    robot_coord[0] = max(-280.0, min(280.0, robot_coord[0]))
    robot_coord[1] = max(-280.0, min(280.0, robot_coord[1]))

    init.open_gripper()
    mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 40)
    time.sleep(3)
    mc.send_coords([robot_coord[0], robot_coord[1], z, -173, 0, -45], 40)
    time.sleep(2)
    init.close_gripper()

    init.current_held_object = object_name
    init.known_objects[object_name] = "in gripper"

    mc.send_coords([robot_coord[0], robot_coord[1], 200, -173, 0, -45], 20)
    time.sleep(3)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)

    return robot_coord


# ── move_to ──────────────────────────────────────────────────────────────────

def raw_move_to(target_coord: list = None, target_name: str = None, target_height: int = 110) -> str:
    """Move and place current object at target_coord or on top of target_name."""
    if target_name and not target_coord:
        if target_name in init.known_objects and isinstance(init.known_objects[target_name], list):
            target_coord = init.known_objects[target_name]
            print(f"🤖 <SYSTEM>: ใช้พิกัดของ '{target_name}' จากความจำ {target_coord}")
        else:
            from vision import yolo_detector
            print(f"🤖 <SYSTEM>: ไม่รู้พิกัดของ '{target_name}' กำลังใช้กล้องสแกนหา...")
            found_coord = yolo_detector.scan_with_yolo(target_name)
            if found_coord:
                target_coord = found_coord
                print(f"🤖 <SYSTEM>: สแกนเจอ '{target_name}' ที่พิกัด {target_coord}")
            else:
                print(f"⚠️ <SYSTEM>: หา '{target_name}' ไม่เจอ! วางไว้ที่เดิม...")
                target_coord = init.last_coords[:2] if init.last_coords else [0, -150]

    if not target_coord:
        print(f"⚠️ <SYSTEM>: ไม่มีพิกัดเป้าหมาย! วางไว้ที่เดิม...")
        target_coord = init.last_coords[:2] if init.last_coords else [0, -150]

    tc = [max(-280.0, min(280.0, float(target_coord[0]))),
          max(-280.0, min(280.0, float(target_coord[1])))]
    th = max(0, min(280, int(target_height)))

    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่พิกัด {tc} ความสูง {th}...")
    mc.send_coords([tc[0], tc[1], 180, -175, 0, -45], 40)
    time.sleep(2.5)
    mc.send_coords([tc[0], tc[1], th, -175, 0, -45], 40)
    time.sleep(2)
    init.open_gripper()
    time.sleep(1)
    mc.send_coords([tc[0], tc[1], 200, -175, 0, -45], 40)
    time.sleep(2)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(1)

    if init.current_held_object:
        init.known_objects[init.current_held_object] = [round(tc[0], 2), round(tc[1], 2)]
        init.current_held_object = None

    print("🤖 <SYSTEM>: วางวัตถุสำเร็จ")
    return "Placed successfully."


# ── show_object ──────────────────────────────────────────────────────────────

def raw_show_object(object_name: str) -> str:
    print(f"🤖 <SYSTEM>: กำลังโชว์ {object_name}...")
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(2)
    mc.send_angles([0, 0, 0, -90, 0, -45], 40)
    time.sleep(2.5)
    return "success"


# ── move ─────────────────────────────────────────────────────────────────────

def raw_move(x: float, y: float, z: float, speed: int = 40) -> str:
    x = max(-280.0, min(280.0, float(x)))
    y = max(-280.0, min(280.0, float(y)))
    z = max(0.0, min(280.0, float(z)))
    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่ (X:{x}, Y:{y}, Z:{z}) ด้วยความเร็ว {speed}...")
    mc.send_coords([x, y, z, -175, 0, -45], speed)
    time.sleep(3)
    return f"Moved to X:{x}, Y:{y}, Z:{z}."


# ── rotate_gripper ───────────────────────────────────────────────────────────

def raw_rotate_gripper(angle_range: int = 45, speed: int = 40) -> str:
    print(f"Rotating gripper by {angle_range} degrees...")
    current = mc.get_angles()
    j6 = current[5] if current and len(current) == 6 else -45
    mc.send_angle(6, j6 + angle_range, speed)
    time.sleep(1.5)
    mc.send_angle(6, j6 - angle_range, speed)
    time.sleep(2.0)
    mc.send_angle(6, j6, speed)
    time.sleep(1.5)
    return "Rotation done."


# ── dance_celebrate ──────────────────────────────────────────────────────────

def raw_dance_celebrate() -> str:
    print("Dancing! 💃")
    speed = 60
    mc.send_angles([-45, 0, -20, 0, 0, -45], speed); time.sleep(1)
    mc.send_angles([45,  0, -20, 0, 0, -45], speed); time.sleep(1)
    mc.send_angles([-45, 0,  30, -30, 0, -45], speed); time.sleep(1)
    mc.send_angles([45,  0,  30, -30, 0, -45], speed); time.sleep(1)
    mc.send_angles([0,   0,   0,   0, 0, -45], speed); time.sleep(1.5)
    return "Dance done."


# ── gesture ──────────────────────────────────────────────────────────────────

def raw_gesture(action: str) -> str:
    action = action.lower()
    if action not in ("yes", "no"):
        return "Error: action must be 'yes' or 'no'."
    print(f"Gesture: {action.upper()}")
    speed = 60
    current = mc.get_angles()
    base = current if current and len(current) == 6 else [0, 0, 0, 0, 0, -45]
    if action == "yes":
        j5 = base[4]
        mc.send_angle(5, j5 + 30, speed); time.sleep(0.5)
        mc.send_angle(5, j5 - 30, speed); time.sleep(0.6)
        mc.send_angle(5, j5 + 30, speed); time.sleep(0.6)
        mc.send_angle(5, j5, speed);      time.sleep(0.5)
        return "Nodded YES."
    else:
        j1 = base[0]
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.5)
        mc.send_angle(1, j1 - 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1, speed);      time.sleep(0.5)
        return "Shook NO."


# ── scan_object ──────────────────────────────────────────────────────────────

def raw_scan_object(object_name: str) -> str:
    from vision import yolo_detector
    yolo_coord = yolo_detector.scan_with_yolo(object_name)
    if yolo_coord:
        init.known_objects[object_name] = yolo_coord
        return f"Found '{object_name}' at {yolo_coord}. Memory updated."
    return f"'{object_name}' not found."
