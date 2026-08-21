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
_face_model = None
_person_model = None


def get_yolo_model(model_type: str = "cube"):
    """
    Get YOLO model instance based on model_type ('cube', 'area', 'face', 'person').
    'cube': cube.pt (for detecting red, green, blue, yellow blocks)
    'area': area.pt (for detecting blue_area, red_area, one_area, two_area, etc.)
    'face': face.pt (for detecting faces)
    'person': person.pt (for detecting people)
    """
    global _cube_model, _area_model, _face_model, _person_model
    if model_type == "face":
        if _face_model is None:
            try:
                from vision.safe_yolo import YOLO
                model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "face.pt")
                if os.path.exists(model_path):
                    _face_model = YOLO(model_path)
                    print(f"🤖 <SYSTEM>: โหลดโมเดลตรวจจับใบหน้า face.pt สำเร็จ")
                else:
                    print(f"⚠️ <SYSTEM>: ไม่พบโมเดล face.pt ที่ {model_path}")
            except Exception as e:
                print(f"⚠️ <SYSTEM>: ไม่สามารถโหลด face.pt: {e}")
        return _face_model
    elif model_type == "person":
        if _person_model is None:
            try:
                from vision.safe_yolo import YOLO
                model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "person.pt")
                if os.path.exists(model_path):
                    _person_model = YOLO(model_path)
                    print(f"🤖 <SYSTEM>: โหลดโมเดลตรวจจับคน person.pt สำเร็จ")
                else:
                    print(f"⚠️ <SYSTEM>: ไม่พบโมเดล person.pt ที่ {model_path}")
            except Exception as e:
                print(f"⚠️ <SYSTEM>: ไม่สามารถโหลด person.pt: {e}")
        return _person_model
    elif model_type == "area":
        if _area_model is None:
            try:
                from vision.safe_yolo import YOLO
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
                from vision.safe_yolo import YOLO
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
        get_yolo_model("face")
        get_yolo_model("person")
    threading.Thread(target=_preload, daemon=True).start()


# Start preloading immediately when module is imported
# preload_model() # REMOVED: Causes Segmentation fault on Jetson due to concurrent Torch CUDA + OpenCV Camera initialization

def classify_cube_color_hsv(crop_bgr) -> str:
    """
    Non-invasive helper: Classify physical color of cropped cube using HSV color space.
    Returns: 'red_cube', 'yellow_cube', 'green_cube', 'blue_cube', or None.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return None
    try:
        h, w = crop_bgr.shape[:2]
        if h < 5 or w < 5:
            return None
        # Center 60% crop to avoid table background and border shadows
        my, mx = int(h * 0.2), int(w * 0.2)
        center = crop_bgr[my:h-my, mx:w-mx]
        if center.size == 0:
            center = crop_bgr

        hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)

        # Red: Hue in 0..10 or 160..180
        mask_red1 = cv2.inRange(hsv, (0, 60, 50), (10, 255, 255))
        mask_red2 = cv2.inRange(hsv, (160, 60, 50), (180, 255, 255))
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Yellow: Hue in 15..38 (Distinct separation from red and green)
        mask_yellow = cv2.inRange(hsv, (15, 60, 50), (38, 255, 255))

        # Green: Hue in 39..85 (Distinct separation from blue)
        mask_green = cv2.inRange(hsv, (39, 50, 40), (85, 255, 255))

        # Blue: Hue in 90..135 (Distinct separation from green)
        mask_blue = cv2.inRange(hsv, (90, 60, 40), (135, 255, 255))

        counts = {
            "red_cube": cv2.countNonZero(mask_red),
            "yellow_cube": cv2.countNonZero(mask_yellow),
            "green_cube": cv2.countNonZero(mask_green),
            "blue_cube": cv2.countNonZero(mask_blue),
        }

        best_color, max_count = max(counts.items(), key=lambda item: item[1])
        total_pixels = center.shape[0] * center.shape[1]

        # Require at least 15% of pixels to match dominant color
        if total_pixels > 0 and max_count > total_pixels * 0.15:
            return best_color
    except Exception:
        pass
    return None


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
    Scans the environment using YOLO model (cube.pt, area.pt, face.pt, or person.pt).
    Returns: robot_coord (list of [x, y]) if found, else None
    """
    name_lower = object_name.lower().strip()
    if any(k in name_lower for k in ("face", "หน้า", "ใบหน้า")):
        primary_type = "face"
    elif any(k in name_lower for k in ("person", "คน", "มนุษย์", "human")):
        primary_type = "person"
    elif is_area_query(object_name):
        primary_type = "area"
    else:
        primary_type = "cube"

    model = get_yolo_model(primary_type)
    if not model:
        model = get_yolo_model("cube")
    if not model:
        return None

    print(f"🤖 <SYSTEM>: เริ่มการสแกนด้วย YOLO ({model.ckpt_path if hasattr(model, 'ckpt_path') else primary_type}) ค้นหา '{object_name}'...")
    scan_angles = armconfig.SCAN_ANGLES

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    time.sleep(0.5)

    # catlazy: reuse _raw.get_english_name แทนการดักคำภาษาไทยยาวเหยียด 30 บรรทัด
    from agent.tools.shares._raw import get_english_name
    eng_name = get_english_name(object_name)
    obj_lower = eng_name.replace("_", " ")
        
    obj_words = set(obj_lower.split())
    colors = {'red', 'green', 'blue', 'yellow', 'orange'}
    obj_colors = obj_words.intersection(colors)

    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO ({primary_type}) หันกล้องไปที่มุม {j1} องศา...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        
        wait_time = getattr(armconfig, 'SCAN_WAIT_PER_ANGLE', 1.5)
        time.sleep(wait_time)

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


            if hasattr(cam_manager, 'set_ai_results') and len(results) > 0:
                cam_manager.set_ai_results(results[0], duration=0.8)

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    name = model.names[cls]

                    # Non-invasive HSV color refinement (only for cube model)
                    if primary_type == "cube" and frame is not None:
                        try:
                            ih, iw = frame.shape[:2]
                            bx_coords = box.xyxy[0].cpu().numpy()
                            bx1, by1 = max(0, int(bx_coords[0])), max(0, int(bx_coords[1]))
                            bx2, by2 = min(iw, int(bx_coords[2])), min(ih, int(bx_coords[3]))
                            if bx2 > bx1 and by2 > by1:
                                verified_name = classify_cube_color_hsv(frame[by1:by2, bx1:bx2])
                                if verified_name and verified_name != name:
                                    print(f"🤖 <SYSTEM>: [Color Correction] ปรับแก้สีจาก '{name}' → '{verified_name}' ด้วยค่าสีจริง (HSV)")
                                    name = verified_name
                        except Exception:
                            pass

                    name_lower = name.lower().replace("_", " ")
                    name_words = set(name_lower.split())
                    name_colors = name_words.intersection(colors)

                    # STRONGER COLOR ENFORCEMENT
                    if obj_colors:
                        # If query has a color, the detected object MUST have that exact color
                        if not name_colors or not obj_colors.intersection(name_colors):
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

                        # Apply global World Offsets for precise grabbing alignment
                        x_world += getattr(armconfig, 'GRAB_X_OFFSET', 0.0)
                        y_world += getattr(armconfig, 'GRAB_Y_OFFSET', 0.0)

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


def detect_boxes_in_frame(frame, j1_angle: float = 0.0, conf_thresh: float = 0.30) -> dict:
    """Detect cubes in a single frame and convert to world robot coordinates [x, y]."""
    cube_model = get_yolo_model("cube")
    if cube_model is None or frame is None:
        return {}

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    found = {}
    try:
        results = cube_model(frame, verbose=False, conf=conf_thresh)
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                name = cube_model.names[cls].lower()
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                # Safe HSV color refinement for cube
                if frame is not None:
                    try:
                        ih, iw = frame.shape[:2]
                        bx1, by1 = max(0, int(x1)), max(0, int(y1))
                        bx2, by2 = min(iw, int(x2)), min(ih, int(y2))
                        if bx2 > bx1 and by2 > by1:
                            verified_name = classify_cube_color_hsv(frame[by1:by2, bx1:bx2])
                            if verified_name:
                                name = verified_name
                    except Exception:
                        pass
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
                    center_x = 640 - center_x

                target_pixel = (center_x, center_y)
                robot_coord_np = eyeonhand.pixel_to_arm(target_pixel)
                robot_coord = [float(robot_coord_np[0]) + x_offset, float(robot_coord_np[1]) + y_offset]

                theta = math.radians(j1_angle)
                x_world = robot_coord[0] * math.cos(theta) - robot_coord[1] * math.sin(theta)
                y_world = robot_coord[0] * math.sin(theta) + robot_coord[1] * math.cos(theta)
                x_world += getattr(armconfig, 'GRAB_X_OFFSET', 0.0)
                y_world += getattr(armconfig, 'GRAB_Y_OFFSET', 0.0)

                x_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x_world))
                y_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y_world))
                coord = [round(x_world, 2), round(y_world, 2)]

                base_name = name
                cnt = 1
                while name in found:
                    cnt += 1
                    name = f"{base_name}_{cnt}"

                found[name] = coord
                init.known_objects[name] = coord
    except Exception as e:
        print(f"⚠️ <SYSTEM>: detect_boxes_in_frame error: {e}")

    return found


def quick_scan_desk_objects(angles: list = None) -> dict:
    """Quickly scan desk from key angles to update real-time positions of all boxes."""
    if angles is None:
        angles = [0, -30, 30]

    print(f"🤖 <SYSTEM>: [Vision Safety] กำลังสแกนตรวจจับกล่องบนโต๊ะแบบ Real-time เพื่อหาพื้นที่ปลอดภัย...")
    found_all = {}

    for j1 in angles:
        target_pose = armconfig.POSE_READY.copy()
        target_pose[0] = target_pose[0] + j1
        mc.send_angles(target_pose, armconfig.SPEED_GRAB)
        time.sleep(0.7)

        for _ in range(2):
            frame = cam_manager.get_frame()
            if frame is not None:
                detected = detect_boxes_in_frame(frame, j1_angle=j1)
                found_all.update(detected)
                break
            time.sleep(0.1)

    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(0.5)

    print(f"🤖 <SYSTEM>: [Vision Safety] สแกนพบกล่องบนโต๊ะทั้งหมด {len(found_all)} จุด: {list(found_all.keys())}")
    return found_all


def verify_and_calibrate_memory() -> dict:
    """
    Scans the desk across all angles and verifies known_objects memory against physical reality 100%.
    - If a cube is moved or displaced (>15mm): Updates its coordinates in known_objects.
    - If a new cube is found: Adds it to known_objects.
    - If a previously remembered cube is missing from the table: Removes it from known_objects.
    Returns:
        dict of verified known_objects
    """
    print("🤖 <SYSTEM>: [Memory Check] เริ่มต้นการตรวจสอบความถูกต้องของความจำเทียบกับตำแหน่งจริง 100%...")
    
    # 1. Quick scan across key desk angles to find all physical cubes
    detected = quick_scan_desk_objects(angles=armconfig.SCAN_ANGLES)
    
    # Track physical cubes found in this scan
    found_cubes = {}
    for obj_name, coord in detected.items():
        if "cube" in obj_name.lower():
            # Standardize key name (e.g. "red_cube_1" -> "red_cube")
            std_color = obj_name.split("_")[0].lower()
            std_name = f"{std_color}_cube"
            found_cubes[std_name] = coord

    # 2. Check each previously known cube
    old_cube_keys = [k for k in list(init.known_objects.keys()) if "cube" in k.lower()]
    
    # Update or add verified cubes
    for cube_name, coord in found_cubes.items():
        old_val = init.known_objects.get(cube_name)
        if old_val and isinstance(old_val, list) and len(old_val) >= 2 and old_val != "in gripper":
            dist = math.hypot(coord[0] - old_val[0], coord[1] - old_val[1])
            if dist > 15.0:
                print(f"🔄 <SYSTEM>: [Memory Check] '{cube_name}' ขยับตำแหน่ง {dist:.1f}mm! ปรับพิกัดจาก {old_val[:2]} -> {coord}")
                init.known_objects[cube_name] = [coord[0], coord[1], armconfig.GRAB_BASE_HEIGHT]
            else:
                print(f"✅ <SYSTEM>: [Memory Check] พิกัด '{cube_name}' ถูกต้อง 100% ตรงกับความเป็นจริง ({coord})")
        else:
            print(f"✨ <SYSTEM>: [Memory Check] พบ '{cube_name}' ใหม่บนโต๊ะ! บันทึกพิกัด {coord}")
            init.known_objects[cube_name] = [coord[0], coord[1], armconfig.GRAB_BASE_HEIGHT]

    # Remove stale cubes that were not seen anywhere in the scan (except currently held object)
    held_obj = init.current_held_object if (init.is_holding_object or init.current_held_object) else None
    for old_k in old_cube_keys:
        if held_obj and (old_k == held_obj or held_obj in old_k or old_k in held_obj):
            continue
        if old_k not in found_cubes:
            print(f"🗑️ <SYSTEM>: [Memory Check] ไม่พบ '{old_k}' บนโต๊ะแล้ว → ลบออกจากความจำเพื่อความถูกต้อง 100%")
            init.known_objects.pop(old_k, None)

    print(f"✅ <SYSTEM>: [Memory Check] ตรวจสอบความจำสมบูรณ์ 100%: {init.known_objects}")
    return init.known_objects


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
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                        # Safe HSV color refinement for cube model
                        if model == cube_model and frame is not None:
                            try:
                                ih, iw = frame.shape[:2]
                                bx1, by1 = max(0, int(x1)), max(0, int(y1))
                                bx2, by2 = min(iw, int(x2)), min(ih, int(y2))
                                if bx2 > bx1 and by2 > by1:
                                    verified_name = classify_cube_color_hsv(frame[by1:by2, bx1:bx2])
                                    if verified_name:
                                        name = verified_name
                            except Exception:
                                pass

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
