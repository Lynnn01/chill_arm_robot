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
_face_model = None
_person_model = None


def get_yolo_model(model_type: str = "cube"):
    """
    Get YOLO model instance based on model_type ('cube', 'face', 'person').
    'cube': cube.pt (for detecting red, green, blue, yellow blocks)
    'face': face.pt (for detecting faces)
    'person': person.pt (for detecting people)
    """
    global _cube_model, _face_model, _person_model
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


def scan_with_yolo(object_name: str = "cube"):
    """
    Unified Central Scanning Function using YOLO + HSV color verification.
    
    Modes:
    1. Targeted Scan (specific color/object, e.g. "red_cube", "face", "person"):
       Bends down to POSE_READY, rotates step-by-step through SCAN_ANGLES (15° steps).
       As soon as the target object is detected and verified, records coordinate in
       known_objects and immediately returns [x, y].
       
    2. Full Desk Scan & Memory Calibration (e.g. "cube", "all", "all_objects", "box", ""):
       Bends down to POSE_READY, rotates through ALL SCAN_ANGLES (15° steps).
       Detects and verifies all physical cubes on the table.
       Calibrates memory 100%:
       - Updates coordinates of moved cubes (>15mm)
       - Adds newly discovered cubes
       - Removes stale/missing cubes (while preserving held object)
       Returns dict of known_objects.
    """
    name_raw = (object_name or "cube").strip()
    name_lower = name_raw.lower()

    if any(k in name_lower for k in ("face", "หน้า", "ใบหน้า")):
        primary_type = "face"
    elif any(k in name_lower for k in ("person", "คน", "มนุษย์", "human")):
        primary_type = "person"
    else:
        primary_type = "cube"

    model = get_yolo_model(primary_type)
    if not model:
        model = get_yolo_model("cube")
    if not model:
        return None

    from agent.tools.shares._raw import get_english_name
    eng_name = get_english_name(name_raw) if name_raw else ""
    obj_lower = eng_name.replace("_", " ").strip() if eng_name else name_lower

    # Determine if this is a general desk scan / memory calibration
    is_full_desk_scan = (
        primary_type == "cube"
        and (
            not obj_lower
            or obj_lower in ("cube", "cubes", "box", "boxes", "all", "all objects", "table", "desk", "สิ่งของ", "กล่อง")
        )
    )

    if is_full_desk_scan:
        print(f"🤖 <SYSTEM>: [Central Scanner] เริ่มต้นการสแกนโต๊ะแบบ Panoramic และตรวจสอบความจำ 100% (ทีละ 15°)...")
    else:
        print(f"🤖 <SYSTEM>: [Central Scanner] เริ่มต้นการสแกนหา '{name_raw}' ({primary_type}) ทีละ 15°...")

    scan_angles = armconfig.SCAN_ANGLES

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)

    time.sleep(0.3)

    obj_words = set(obj_lower.split())
    colors = {'red', 'green', 'blue', 'yellow', 'orange'}
    obj_colors = obj_words.intersection(colors)

    found_cubes = {}
    conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
    wait_time = getattr(armconfig, "SCAN_WAIT_PER_ANGLE", 1.5)

    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO หันกล้องไปที่มุม {j1} องศา (ค้างรอ {wait_time}s)...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(wait_time)

        for attempt in range(2):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            results = model(frame, verbose=False, conf=conf_thresh)
            if hasattr(cam_manager, 'set_ai_results') and len(results) > 0:
                cam_manager.set_ai_results(results[0], duration=0.8)

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    name = model.names[cls]

                    # Non-invasive HSV color refinement for cube model
                    if primary_type == "cube" and frame is not None:
                        try:
                            ih, iw = frame.shape[:2]
                            bx_coords = box.xyxy[0].cpu().numpy()
                            bx1, by1 = max(0, int(bx_coords[0])), max(0, int(bx_coords[1]))
                            bx2, by2 = min(iw, int(bx_coords[2])), min(ih, int(bx_coords[3]))
                            if bx2 > bx1 and by2 > by1:
                                verified_name = classify_cube_color_hsv(frame[by1:by2, bx1:bx2])
                                if verified_name and verified_name != name:
                                    name = verified_name
                        except Exception:
                            pass

                    name_lower = name.lower().replace("_", " ")
                    name_words = set(name_lower.split())
                    name_colors = name_words.intersection(colors)

                    # Calculate world coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2

                    if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
                        center_x = 640 - center_x

                    target_pixel = (center_x, center_y)
                    robot_coord_np = eyeonhand.pixel_to_arm(target_pixel)
                    robot_coord = [float(robot_coord_np[0]) + x_offset, float(robot_coord_np[1]) + y_offset]

                    theta = math.radians(j1)
                    x_local = float(robot_coord[0])
                    y_local = float(robot_coord[1])

                    x_world = x_local * math.cos(theta) - y_local * math.sin(theta)
                    y_world = x_local * math.sin(theta) + y_local * math.cos(theta)

                    x_world += getattr(armconfig, 'GRAB_X_OFFSET', 0.0)
                    y_world += getattr(armconfig, 'GRAB_Y_OFFSET', 0.0)

                    x_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, x_world))
                    y_world = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, y_world))
                    saved_coord = [round(x_world, 2), round(y_world, 2)]

                    # Standardize cube key (e.g. "red_cube")
                    std_name = name.lower()
                    if "_" not in std_name and primary_type == "cube":
                        std_name = f"{std_name}_cube"

                    # 1. Full Desk Scan Mode: Aggregate all cubes
                    if is_full_desk_scan:
                        found_cubes[std_name] = saved_coord

                    # 2. Targeted Scan Mode: Match requested object and return immediately
                    else:
                        if obj_colors:
                            if not name_colors or not obj_colors.intersection(name_colors):
                                continue
                        if obj_words.intersection(name_words) or any(w in name_lower for w in obj_words if len(w) > 2):
                            print(f"🤖 <SYSTEM>: YOLO ({primary_type}) เจอ '{std_name}' ที่มุม {j1}! พิกัดโลก: {saved_coord}")
                            mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
                            init.known_objects[std_name] = [saved_coord[0], saved_coord[1], armconfig.GRAB_BASE_HEIGHT]
                            return saved_coord

            time.sleep(0.1)

    # ── Post-Scan Processing ───────────────────────────────────────────────────
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(0.5)

    # Full Desk Scan: Re-calibrate memory 100%
    if is_full_desk_scan:
        old_cube_keys = [k for k in list(init.known_objects.keys()) if "cube" in k.lower()]
        held_obj = init.current_held_object if (init.is_holding_object or init.current_held_object) else None

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

        # Remove stale cubes not seen anywhere (except held cube)
        for old_k in old_cube_keys:
            if held_obj and (old_k == held_obj or held_obj in old_k or old_k in held_obj):
                continue
            if old_k not in found_cubes:
                print(f"🗑️ <SYSTEM>: [Memory Check] ไม่พบ '{old_k}' บนโต๊ะแล้ว → ลบออกจากความจำเพื่อความถูกต้อง 100%")
                init.known_objects.pop(old_k, None)

        print(f"✅ <SYSTEM>: [Central Scanner] สแกนครบถ้วน ความจำสมบูรณ์ 100%: {init.known_objects}")
        return init.known_objects

    print(f"🤖 <SYSTEM>: YOLO สแกนครบ {len(scan_angles)} มุมแล้ว ไม่พบ '{name_raw}'")
    return None


# Centralized alias for direct memory calibration calls
def verify_and_calibrate_memory() -> dict:
    """Re-scan entire desk and re-calibrate known_objects memory 100%. Returns updated known_objects dict."""
    return scan_with_yolo("cube")
