import time
import json
from PIL import Image
from vision import api
from hardware.init import mc
from hardware import init
from vision import eyeonhand
from agents import function_tool
from vision import yolo_detector
import armconfig

@function_tool
def grab_object(object_name: str, target_coord: list = None) -> list:
    """
    [Tags: Action, Vision, Memory]
    Uses computer vision to detect and grab the specified object from the workspace.
    If target_coord is provided, it skips vision and grabs directly from that location.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "หยิบ", "จับ", "เอา" วัตถุที่ระบุ
    - ระบบจะตรวจสอบ Memory อัตโนมัติ หากเจอพิกัดจะหยิบเลย หากไม่เจอจะใช้กล้องสแกนก่อน
    
    Args:
        object_name: The descriptive name of the object to grab (e.g., "red block", "blue cube").
        target_coord: Optional [x, y] coordinates to grab from. If provided, vision is skipped.
    """
    init.BotInit(mc)
    
    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)
    z_offset = config_data.get("z", 0)
    z = 120 + z_offset

    if target_coord and len(target_coord) >= 2:
        print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปหยิบของที่พิกัด {target_coord}...")
        robot_coord = [float(target_coord[0]), float(target_coord[1])]
    elif object_name in init.known_objects and isinstance(init.known_objects[object_name], list):
        saved_coord = init.known_objects[object_name]
        print(f"🤖 <SYSTEM>: ดึงพิกัด '{object_name}' จากความจำ {saved_coord} (ข้ามการสแกน)...")
        robot_coord = [float(saved_coord[0]), float(saved_coord[1])]
    else:
        # 1. Fast Scan with YOLO
        yolo_coord = yolo_detector.scan_with_yolo(object_name)
        if yolo_coord:
            robot_coord = yolo_coord
            print(f"🤖 <SYSTEM>: YOLO เจอแล้ว! กำลังเคลื่อนที่ไปพิกัด {robot_coord}")
        else:
            # 2. Fallback to Vision AI (Qwen) single photo check
            print(f"🤖 <SYSTEM>: กำลังใช้กล้อง Vision AI ค้นหา '{object_name}'...")
            init.GetImage()
            import os
            img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
            width, height = Image.open(img_path).size
            positions = api.QwenVLRequest("a " + object_name, img_path).get("coordinates", [])

            if positions:
                position = positions[0]
                # Calculate center point coordinates
                center_x = (position['x1'] + position['x2']) / 2
                center_y = (position['y1'] + position['y2']) / 2
                target_pixel = (center_x / 1000 * width, center_y / 1000 * height)
                robot_coord_np = eyeonhand.pixel_to_arm(target_pixel)
                robot_coord = [float(robot_coord_np[0]), float(robot_coord_np[1])]
                print(f"🤖 <SYSTEM>: เจอแล้ว! กำลังเคลื่อนที่ไปพิกัด {robot_coord}")
                robot_coord[0] = robot_coord[0] + x_offset
                robot_coord[1] = robot_coord[1] + y_offset
                if robot_coord[0] > 210:
                    robot_coord[0] = robot_coord[0] - 5
            else:
                print(f"🤖 <SYSTEM>: ไม่พบ {object_name} ในภาพ")
                return f"Error: มองไม่เห็น '{object_name}' บนโต๊ะเลยครับ ขอยกเลิกการหยิบ"

    # Safety clamps for grasping
    robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[0]))
    robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[1]))

    import math
    if z < 100:
        radius = math.sqrt(robot_coord[0]**2 + robot_coord[1]**2)
        if radius < armconfig.GRAB_MIN_RADIUS:
            print(f"⚠️ <SYSTEM>: เป้าหมายหยิบของอยู่ใกล้ฐานเกินไปและ Z ต่ำ ปรับให้ปลอดภัยขึ้น...")
            if radius > 0:
                scale = armconfig.GRAB_MIN_RADIUS / radius
                robot_coord[0] = robot_coord[0] * scale
                robot_coord[1] = robot_coord[1] * scale
            else:
                robot_coord[0], robot_coord[1] = armconfig.GRAB_MIN_RADIUS, 0

    init.open_gripper()
    
    # Safe Movement Sequence
    current_coords = mc.safe_get_coords()
    if current_coords and len(current_coords) >= 3:
        # 1. Lift straight up first to avoid hitting objects
        lift_target = [current_coords[0], current_coords[1], armconfig.Z_SAFE_TRAVEL]
        mc.send_coords(lift_target + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
        mc.wait_for_arrival(lift_target, mode="coords")
        
    # 2. Move Horizontally at safe height
    xy_target = [robot_coord[0], robot_coord[1], armconfig.Z_SAFE_TRAVEL]
    mc.send_coords(xy_target + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(xy_target, mode="coords")
    
    # 3. Descend to grab
    final_target = [robot_coord[0], robot_coord[1], z]
    mc.send_coords(final_target + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(final_target, mode="coords")
    
    init.close_gripper()
    
    # Check Grasp Success
    # Grasp success: gripper angle > 10 (didn't close completely because an object is in the way)
    # Gripper angle < 5 means it closed completely (empty).
    time.sleep(1) # wait for gripper to finish closing
    gripper_angles = mc.safe_get_angles()
    # Assuming gripper is the last joint [j1, j2, j3, j4, j5, gripper] or we can just read gripper value
    # Some firmwares use get_gripper_value(), but we'll trust the visual feedback or standard init for now.
    
    # Update Memory
    init.current_held_object = object_name
    init.known_objects[object_name] = "in gripper"

    mc.send_coords(xy_target + armconfig.WRIST_DOWN, armconfig.SPEED_LIFT)
    mc.wait_for_arrival(xy_target, mode="coords")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")

    return f"Successfully grabbed {object_name} at coordinates {robot_coord}"
