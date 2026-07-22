import os
import time
import math
from hardware import init
from hardware.init import mc, cam_manager
from vision import eyeonhand
import armconfig

# Lazy load model
_model = None


def get_yolo_model():
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO

            model_path = os.path.join(
                init.PROJECT_ROOT, "vision", "models", "cube.pt"
            )
            if os.path.exists(model_path):
                _model = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
        except ImportError:
            print("⚠️ <SYSTEM>: ไม่พบไลบรารี ultralytics (pip install ultralytics)")
    return _model

def preload_model():
    """Load model in background to avoid delay on first use"""
    import threading
    threading.Thread(target=get_yolo_model, daemon=True).start()

# Start preloading immediately when module is imported
preload_model()


def scan_with_yolo(object_name):
    """
    Scans the environment using YOLO model first.
    Returns: robot_coord (list of [x, y]) if found, else None
    """
    model = get_yolo_model()
    if not model:
        return None

    print(f"🤖 <SYSTEM>: เริ่มการสแกนเร็วด้วย YOLO ค้นหา '{object_name}'...")
    scan_angles = armconfig.SCAN_ANGLES

    import json

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    # ลดเวลาการรอเริ่มต้นให้เร็วขึ้น
    time.sleep(0.5)

    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO หันกล้องไปที่มุม {j1} องศา...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(1.5)

        # ให้โอกาส YOLO สแกน 3 เฟรมที่มุมนี้ เผื่อภาพเบลอจากกล้องที่เพิ่งหยุดหมุน
        found = False
        for attempt in range(3):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

        # ใช้ conf=0.15 เพื่อเพิ่มความไวในการดักจับ (บางทีแสงหรือมุมทำให้ความมั่นใจต่ำลง) หรือใช้จาก armconfig ถ้าตั้งไว้
        conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
        results = model(frame, verbose=False, conf=conf_thresh)
        annotated_frame = results[0].plot()
        # แสดง Overlay ซ้อนภาพ แต่ไม่บังคับหยุดรอถ้ายังไม่เจอของ
        cam_manager.set_overlay(annotated_frame, duration=1.0)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                name = model.names[cls]

                # Simple matching logic: if any word matches
                obj_lower = object_name.lower().replace("_", " ")
                name_lower = name.lower().replace("_", " ")

                thai_map = {
                    "แดง": "red",
                    "เขียว": "green",
                    "น้ำเงิน": "blue",
                    "ฟ้า": "blue",
                    "เหลือง": "yellow",
                    "ส้ม": "orange",
                    "กล่อง": "cube",
                    "บล็อก": "cube",
                    "สี": "",
                }
                for th, en in thai_map.items():
                    obj_lower = obj_lower.replace(th, f" {en} ")

                obj_words = set(obj_lower.split())
                name_words = set(name_lower.split())
                
                colors = {'red', 'green', 'blue', 'yellow', 'orange'}
                obj_colors = obj_words.intersection(colors)
                name_colors = name_words.intersection(colors)
                
                # If both specify a color, they must match exactly
                if obj_colors and name_colors and not obj_colors.intersection(name_colors):
                    continue
                
                # Check for direct match or substring match
                if obj_words.intersection(name_words):
                    # Found!
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    
                    if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
                        center_x = 640 - center_x

                    target_pixel = (center_x, center_y)
                    robot_coord_np = eyeonhand.pixel_to_arm(target_pixel)
                    robot_coord = [float(robot_coord_np[0]), float(robot_coord_np[1])]

                    robot_coord[0] = robot_coord[0] + x_offset
                    robot_coord[1] = robot_coord[1] + y_offset

                    theta = math.radians(j1)
                    x_local = float(robot_coord[0])
                    y_local = float(robot_coord[1])

                    x_world = x_local * math.cos(theta) - y_local * math.sin(theta)
                    y_world = x_local * math.sin(theta) + y_local * math.cos(theta)

                    robot_coord[0] = x_world
                    robot_coord[1] = y_world

                    robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[0]))
                    robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[1]))

                    saved_coord = [round(robot_coord[0], 2), round(robot_coord[1], 2)]

                    print(
                        f"🤖 <SYSTEM>: YOLO เจอ '{name}' ที่มุม {j1}! พิกัดโลก: {saved_coord}"
                    )
                    # หน่วงเวลาสั้นๆ ให้ผู้ใช้เห็นกรอบ
                    time.sleep(1.0)
                    # Return to center
                    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
                    time.sleep(1.0)
                    return saved_coord
            
            # End of box loop
            if found:
                break
                
            time.sleep(0.1)  # รอ 0.1 วิแล้วดึงภาพใหม่มาเช็คอีกรอบ

    print(
        f"🤖 <SYSTEM>: YOLO สแกนครบ 5 มุมแล้ว ไม่พบ '{object_name}' (จะสลับไปใช้ Vision AI API)"
    )
    # Return to center for the next stage
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(1)
    return None

def scan_all_objects():
    """
    Scans the entire environment across multiple angles and returns a dictionary of all detected objects.
    Returns: dict format {"color block": [x, y], ...}
    """
    model = get_yolo_model()
    if not model:
        return {}

    print("🤖 <SYSTEM>: เริ่มการสแกนแบบ Panoramic เพื่อหาวัตถุทั้งหมดบนโต๊ะ...")
    scan_angles = armconfig.SCAN_ANGLES

    import json
    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    found_objects = {}

    for j1 in scan_angles:
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        # We need to wait for arrival for smooth scanning, but yolo_detector uses simple sleep for now
        # We'll use safe_get_coords logic or just wait
        time.sleep(1.5)

        for attempt in range(3):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
            results = model(frame, verbose=False, conf=conf_thresh)
            annotated_frame = results[0].plot()
            cam_manager.set_overlay(annotated_frame, duration=0.5)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                name = model.names[cls]
                
                # If we already recorded this object type and we just want one of each color, we might skip.
                # But what if there are multiple? For now, we record uniquely by color name + index if needed.
                # Since YOLO names are just "red", "blue", let's append " block"
                full_name = name.lower() + " block"
                
                # To handle multiple blocks of the same color, we append a number if it already exists
                base_name = full_name
                count = 1
                while full_name in found_objects:
                    count += 1
                    full_name = f"{base_name} {count}"

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
                    center_x = 640 - center_x

                target_pixel = (center_x, center_y)
                robot_coord_np = eyeonhand.pixel_to_arm(target_pixel)
                robot_coord = [float(robot_coord_np[0]) + x_offset, float(robot_coord_np[1]) + y_offset]

                theta = math.radians(j1)
                x_local = robot_coord[0]
                y_local = robot_coord[1]

                x_world = x_local * math.cos(theta) - y_local * math.sin(theta)
                y_world = x_local * math.sin(theta) + y_local * math.cos(theta)

                if x_world > 210:
                    x_world -= 5

                x_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x_world))
                y_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y_world))

                saved_coord = [round(x_world, 2), round(y_world, 2)]
                found_objects[full_name] = saved_coord
            
            time.sleep(0.1)  # รอเฟรมใหม่เผื่อมีอะไรที่จับได้เพิ่มในมุมเดิม

    # Return to center
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(1.0)
    
    print(f"🤖 <SYSTEM>: สแกนเสร็จสิ้น พบวัตถุทั้งหมด {len(found_objects)} ชิ้น: {found_objects}")
    return found_objects
