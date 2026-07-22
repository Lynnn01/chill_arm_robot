"""
agent/tools/_raw.py — Raw (unwrapped) tool functions for executor.py

These are the actual Python logic functions without the @function_tool decorator,
so executor.py can call them directly without going through openai-agents async machinery.
"""

import time
import json
from hardware.init import mc
from hardware import init
import armconfig


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
    z = armconfig.GRAB_BASE_HEIGHT + z_offset

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
                return {"status": "ERROR", "message": f"ไม่พบ {object_name} ในภาพ"}

    robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[0]))
    robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[1]))

    init.open_gripper()
    mc.send_coords([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL], mode="coords")
    
    print(f"🤖 <SYSTEM>: กำลังพุ่งหัวลงไปหยิบที่ Z={z}...")
    mc.send_coords([robot_coord[0], robot_coord[1], z] + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_z(z)   # รอเฉพาะแกน Z — ไม่สนใจ XY drift
    
    init.close_gripper()
    time.sleep(1)  # รอกริปเปอร์หนีบเสร็จ

    init.current_held_object = object_name
    init.known_objects[object_name] = "in gripper"

    mc.send_coords([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_DOWN, armconfig.SPEED_LIFT)
    mc.wait_for_arrival([robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL], mode="coords")
    
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
        
    print(f"✅ <SYSTEM>: DONE TASK - {object_name}")

    return {"status": "DONE TASK", "data": robot_coord}


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
                init.known_objects[target_name] = [target_coord[0], target_coord[1], armconfig.STACK_BASE_HEIGHT]
                print(f"🤖 <SYSTEM>: สแกนเจอ '{target_name}' ที่พิกัด {target_coord}")
            else:
                print(f"⚠️ <SYSTEM>: หา '{target_name}' ไม่เจอ! วางไว้ที่เดิม...")
                target_coord = init.last_coords[:2] if init.last_coords else [0, -150]

    if not target_coord:
        print(f"⚠️ <SYSTEM>: ไม่มีพิกัดเป้าหมาย! วางไว้ที่เดิม...")
        target_coord = init.last_coords[:2] if init.last_coords else [0, -150]

    # Auto-adjust height for stacking if target_height is default 110
    if target_height == 110:
        stack_count = 0
        for obj_name, coord in init.known_objects.items():
            if isinstance(coord, list) and len(coord) >= 2:
                # Check if coordinates are close (within proximity threshold)
                dx = abs(coord[0] - target_coord[0])
                dy = abs(coord[1] - target_coord[1])
                if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                    stack_count += 1
        
        if stack_count > 0:
            target_height = armconfig.STACK_BASE_HEIGHT + (stack_count * armconfig.STACK_HEIGHT_PER_LAYER) + armconfig.STACK_SAFE_OFFSET
            print(f"🤖 <SYSTEM>: ตรวจพบวัตถุที่พิกัดนี้ {stack_count} ชิ้น ปรับความสูงการวางเป็น {target_height} เพื่อไม่ให้กดทับรุนแรง")

    tc = [max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[0]) + armconfig.STACK_X_OFFSET)),
          max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[1]) + armconfig.STACK_Y_OFFSET))]
    th = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, int(target_height)))

    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่พิกัด {tc} ความสูง {th}...")
    mc.send_coords([tc[0], tc[1], armconfig.Z_PRE_PLACE] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2.5)
    mc.send_coords([tc[0], tc[1], th] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2)
    init.open_gripper()
    time.sleep(1)
    mc.send_coords([tc[0], tc[1], armconfig.Z_SAFE_TRAVEL] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    time.sleep(2)
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")

    if init.current_held_object:
        init.known_objects[init.current_held_object] = [round(tc[0], 2), round(tc[1], 2), th]
        init.current_held_object = None

    print(f"✅ <SYSTEM>: DONE TASK - Placed at {tc}")
    return {"status": "DONE TASK", "message": "Placed successfully."}


# ── show_object ──────────────────────────────────────────────────────────────

def raw_show_object(object_name: str) -> str:
    print(f"🤖 <SYSTEM>: กำลังโชว์ {object_name}...")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(2)
    mc.send_angles(armconfig.POSE_SHOW, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_SHOW, mode="angles")
        
    time.sleep(2) # โชว์ค้างไว้ 2 วิ
    print(f"✅ <SYSTEM>: DONE TASK - Show {object_name}")
    return {"status": "DONE TASK"}


# ── move ─────────────────────────────────────────────────────────────────────

def raw_move(x: float, y: float, z: float, speed: int = 40) -> str:
    from modules.robot_arm.domain.coordinates import TargetCoordinate
    target = TargetCoordinate(x, y, z)
    x, y, z = target.x, target.y, target.z
    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่ (X:{x:.1f}, Y:{y:.1f}, Z:{z:.1f}) ด้วยความเร็ว {speed}...")
    mc.send_coords([x, y, z] + armconfig.WRIST_PLACE, speed)
    mc.wait_for_arrival([x, y, z], mode="coords")
        
    print(f"✅ <SYSTEM>: DONE TASK - Moved to {x:.1f}, {y:.1f}, {z:.1f}")
    return {"status": "DONE TASK"}


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
    if action not in ("yes", "no"):
        return "Error: action must be 'yes' or 'no'."
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
    else:
        j1 = base[0]
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.5)
        mc.send_angle(1, j1 - 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1 + 30, speed); time.sleep(0.6)
        mc.send_angle(1, j1, speed);      time.sleep(0.5)
        print(f"✅ <SYSTEM>: DONE TASK - Gesture NO")
        return {"status": "DONE TASK"}


# ── scan_object ──────────────────────────────────────────────────────────────

def raw_scan_object(object_name: str) -> str:
    from vision import yolo_detector
    yolo_coord = yolo_detector.scan_with_yolo(object_name)
    if yolo_coord:
        init.known_objects[object_name] = yolo_coord
        print(f"✅ <SYSTEM>: DONE TASK - Scan {object_name}")
        return {"status": "DONE TASK", "message": f"Found '{object_name}' at {yolo_coord}. Memory updated."}
    return {"status": "ERROR", "message": f"'{object_name}' not found."}
