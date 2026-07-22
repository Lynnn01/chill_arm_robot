import os
import time
import math
import json
import cv2
from hardware import init
from hardware.init import mc, cam_manager
from vision import eyeonhand
import armconfig

# Lazy load models
_cube_model = None
_area_model = None


def get_yolo_model(model_type: str = "cube"):
    """
    Get YOLO model instance based on model_type ('cube' or 'area').
    'cube': cube.pt (for detecting red, green, blue, yellow blocks)
    'area': area.pt (for detecting blue_area, red_area, one_area, two_area, etc.)
    """
    global _cube_model, _area_model
    if model_type == "area":
        if _area_model is None:
            try:
                from ultralytics import YOLO
                model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "area.pt")
                if os.path.exists(model_path):
                    _area_model = YOLO(model_path)
                    print(f"🤖 <SYSTEM>: โหลดโมเดลระบุพื้นที่ area.pt สำเร็จ ({len(_area_model.names)} คลาส)")
                else:
                    print(f"⚠️ <SYSTEM>: ไม่พบโมเดล area.pt ที่ {model_path}")
            except Exception as e:
                print(f"⚠️ <SYSTEM>: ไม่สามารถโหลด area.pt: {e}")
        return _area_model
    else:
        if _cube_model is None:
            try:
                from ultralytics import YOLO
                model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "cube.pt")
                if os.path.exists(model_path):
                    _cube_model = YOLO(model_path)
                    print(f"🤖 <SYSTEM>: โหลดโมเดลวัตถุ cube.pt สำเร็จ")
                else:
                    print(f"⚠️ <SYSTEM>: ไม่พบโมเดล cube.pt ที่ {model_path}")
            except Exception as e:
                print(f"⚠️ <SYSTEM>: ไม่สามารถโหลด cube.pt: {e}")
        return _cube_model


def preload_model():
    """Load models in background to avoid delay on first use"""
    import threading
    def _preload():
        get_yolo_model("cube")
        get_yolo_model("area")
    threading.Thread(target=_preload, daemon=True).start()


# Start preloading immediately when module is imported
preload_model()


def is_area_query(object_name: str) -> bool:
    """Check if object_name is requesting a target placement area."""
    name_lower = object_name.lower().strip()
    area_keywords = [
        "area", "พื้นที่", "เขต", "โซน", "zone", "one_area", "two_area",
        "three_area", "four_area", "recycle", "danger", "wet", "blank", "general"
    ]
    return any(kw in name_lower for kw in area_keywords)


def scan_with_yolo(object_name: str):
    """
    Scans the environment using YOLO model (cube.pt or area.pt).
    Returns: robot_coord (list of [x, y]) if found, else None
    """
    use_area = is_area_query(object_name)
    primary_type = "area" if use_area else "cube"
    model = get_yolo_model(primary_type)
    if not model:
        model = get_yolo_model("cube" if primary_type == "area" else "area")
    if not model:
        return None

    print(f"🤖 <SYSTEM>: เริ่มการสแกนด้วย YOLO ({model.ckpt_path if hasattr(model, 'ckpt_path') else primary_type}) ค้นหา '{object_name}'...")
    scan_angles = armconfig.SCAN_ANGLES

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    time.sleep(0.5)

    area_thai_map = {
        "พื้นที่ 1": "one_area", "พื้นที่1": "one_area", "โซน 1": "one_area", "โซน1": "one_area",
        "พื้นที่ 2": "two_area", "พื้นที่2": "two_area", "โซน 2": "two_area", "โซน2": "two_area",
        "พื้นที่ 3": "three_area", "พื้นที่3": "three_area", "โซน 3": "three_area", "โซน3": "three_area",
        "พื้นที่ 4": "four_area", "พื้นที่4": "four_area", "โซน 4": "four_area", "โซน4": "four_area",
        "พื้นที่สีแดง": "red_area", "พื้นที่แดง": "red_area",
        "พื้นที่สีเขียว": "green_area", "พื้นที่เขียว": "green_area",
        "พื้นที่สีฟ้า": "blue_area", "พื้นที่สีน้ำเงิน": "blue_area", "พื้นที่ฟ้า": "blue_area",
        "พื้นที่สีเหลือง": "yellow_area", "พื้นที่เหลือง": "yellow_area",
        "พื้นที่รีไซเคิล": "recycle_area", "พื้นที่อันตราย": "danger_area",
        "พื้นที่เปียก": "wet_area", "พื้นที่ว่าง": "blank_area", "พื้นที่ทั่วไป": "general_araa",
    }

    obj_lower = object_name.lower().replace("_", " ")
    for th, en in area_thai_map.items():
        if th in object_name:
            obj_lower = en.replace("_", " ")
            break
            
    thai_map = {
        "แดง": "red", "เขียว": "green", "น้ำเงิน": "blue",
        "ฟ้า": "blue", "เหลือง": "yellow", "ส้ม": "orange",
        "กล่อง": "cube", "บล็อก": "cube", "สี": "",
    }
    for th, en in thai_map.items():
        obj_lower = obj_lower.replace(th, f" {en} ")
        
    obj_words = set(obj_lower.split())
    colors = {'red', 'green', 'blue', 'yellow', 'orange'}
    obj_colors = obj_words.intersection(colors)

    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO ({primary_type}) หันกล้องไปที่มุม {j1} องศา...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(1.5)

        found = False
        for attempt in range(3):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
            if primary_type == "area":
                conf_thresh = min(conf_thresh, 0.25)

            # 1. Try standard frame
            results = model(frame, verbose=False, conf=conf_thresh)
            boxes_found = len(results[0].boxes) if results and len(results) > 0 else 0

            # 2. If no boxes found, test horizontally un-mirrored frame (cv2.flip) to un-reverse text & numbers
            if boxes_found == 0:
                unmirrored_frame = cv2.flip(frame, 1)
                results_unmirrored = model(unmirrored_frame, verbose=False, conf=conf_thresh)
                if results_unmirrored and len(results_unmirrored) > 0 and len(results_unmirrored[0].boxes) > 0:
                    results = results_unmirrored
                    frame = unmirrored_frame

            annotated_frame = results[0].plot()
            cam_manager.set_overlay(annotated_frame, duration=1.0)

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    name = model.names[cls]

                    name_lower = name.lower().replace("_", " ")
                    name_words = set(name_lower.split())
                    name_colors = name_words.intersection(colors)

                    if obj_colors and name_colors and not obj_colors.intersection(name_colors):
                        continue

                    # Check match between query and detected class name
                    if obj_words.intersection(name_words) or any(w in name_lower for w in obj_words if len(w) > 2):
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

                        robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x_world))
                        robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y_world))

                        saved_coord = [round(robot_coord[0], 2), round(robot_coord[1], 2)]

                        print(f"🤖 <SYSTEM>: YOLO ({primary_type}) เจอ '{name}' ที่มุม {j1}! พิกัดโลก: {saved_coord}")
                        time.sleep(1.0)
                        mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
                        time.sleep(1.0)

                        # Remember coordinate in global memory init.known_objects (English only)
                        init.known_objects[name] = saved_coord
                        return saved_coord

            time.sleep(0.1)
        
        # Wait 1.5s before turning to the next angle, EXCEPT 0 degrees
        if j1 != 0:
            time.sleep(1.5)

    print(f"🤖 <SYSTEM>: YOLO สแกนครบ {len(scan_angles)} มุมแล้ว ไม่พบ '{object_name}'")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(1.0)
    return None


def scan_all_objects():
    """
    Scans environment across multiple angles and returns a dictionary of all detected objects and placement areas.
    """
    cube_model = get_yolo_model("cube")
    area_model = get_yolo_model("area")

    print("🤖 <SYSTEM>: เริ่มการสแกนแบบ Panoramic เพื่อหาวัตถุและพื้นที่ทั้งหมด...")
    scan_angles = armconfig.SCAN_ANGLES

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    found_objects = {}

    for j1 in scan_angles:
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(1.5)

        for attempt in range(2):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
            
            # Detect using both models if loaded
            for model in filter(None, [cube_model, area_model]):
                results = model(frame, verbose=False, conf=conf_thresh)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        cls = int(box.cls[0])
                        name = model.names[cls]
                        full_name = name.lower()

                        if "area" not in full_name:
                            full_name += " block"

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
                        x_world = robot_coord[0] * math.cos(theta) - robot_coord[1] * math.sin(theta)
                        y_world = robot_coord[0] * math.sin(theta) + robot_coord[1] * math.cos(theta)

                        x_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x_world))
                        y_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y_world))

                        saved_coord = [round(x_world, 2), round(y_world, 2)]
                        found_objects[full_name] = saved_coord
                        # Also save to global init.known_objects memory
                        init.known_objects[full_name] = saved_coord

            time.sleep(0.1)

    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(1.0)

    print(f"🤖 <SYSTEM>: สแกนเสร็จสิ้น พบวัตถุและพื้นที่ทั้งหมด {len(found_objects)} รายการ: {found_objects}")
    return found_objects
