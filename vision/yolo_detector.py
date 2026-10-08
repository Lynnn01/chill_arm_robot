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


def _hsv_color_counts(crop_bgr):
    """Pixel counts per cube color in the center 70% of the crop. Returns (counts, total) or None."""
    if crop_bgr is None or crop_bgr.size == 0:
        return None
    try:
        h, w = crop_bgr.shape[:2]
        if h < 5 or w < 5:
            return None
        # Center 70% crop to avoid table background and border shadows
        my, mx = int(h * 0.15), int(w * 0.15)
        center = crop_bgr[my:h-my, mx:w-mx]
        if center.size == 0:
            center = crop_bgr

        hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)

        # Red: Hue in 0..11 or 158..180 (S>=40, V>=40)
        mask_red1 = cv2.inRange(hsv, (0, 40, 40), (11, 255, 255))
        mask_red2 = cv2.inRange(hsv, (158, 40, 40), (180, 255, 255))
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Yellow: Hue in 12..32, S>=35, V>=40 (Resistant to desk lamp glare and pale yellow)
        mask_yellow = cv2.inRange(hsv, (12, 35, 40), (32, 255, 255))

        # Green: Hue in 33..88, S>=35, V>=30 (Resistant to shadows; lime/warm green starts at H~33).
        # Bands must NOT overlap with yellow, otherwise a lime-green cube is counted for both colors.
        mask_green = cv2.inRange(hsv, (33, 35, 30), (88, 255, 255))

        # Blue: Hue in 89..138, S>=40, V>=30
        mask_blue = cv2.inRange(hsv, (89, 40, 30), (138, 255, 255))

        counts = {
            "red_cube": cv2.countNonZero(mask_red),
            "yellow_cube": cv2.countNonZero(mask_yellow),
            "green_cube": cv2.countNonZero(mask_green),
            "blue_cube": cv2.countNonZero(mask_blue),
        }

        return counts, center.shape[0] * center.shape[1]
    except Exception as e:
        print(f"⚠️ <SYSTEM>: HSV count failed: {e}")
        return None


def _dominant_color(counts: dict, total_pixels: int):
    """Dominant color name, or None when it covers < 10% of pixels (or < 8 pixels)."""
    best_color, max_count = max(counts.items(), key=lambda item: item[1])
    if total_pixels > 0 and max_count >= 8 and max_count > total_pixels * 0.10:
        return best_color
    return None


def classify_cube_color_hsv(crop_bgr) -> str:
    """
    Non-invasive helper: Classify physical color of cropped cube using HSV color space.
    Tuned for real-world lighting: glare resistance, lime/warm green, pale yellow.
    Returns: 'red_cube', 'yellow_cube', 'green_cube', 'blue_cube', or None.
    """
    res = _hsv_color_counts(crop_bgr)
    return _dominant_color(*res) if res else None


def _announce_scan(is_full_desk_scan: bool, name_raw: str, primary_type: str) -> None:
    if is_full_desk_scan:
        print(f"🤖 <SYSTEM>: [Central Scanner] เริ่มต้นการสแกนโต๊ะแบบ Panoramic และตรวจสอบความจำ 100% (ทีละ 15°)...")
    else:
        print(f"🤖 <SYSTEM>: [Central Scanner] เริ่มต้นการสแกนหา '{name_raw}' ({primary_type}) ทีละ 15°...")


def _load_xy_offsets():
    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    return config_data.get("x", 0), config_data.get("y", 0)


def _primary_type(name_lower: str) -> str:
    if any(k in name_lower for k in ("face", "หน้า", "ใบหน้า")):
        return "face"
    if any(k in name_lower for k in ("person", "คน", "มนุษย์", "human")):
        return "person"
    return "cube"


def _is_full_desk_scan(primary_type: str, obj_lower: str) -> bool:
    return (
        primary_type == "cube"
        and (
            not obj_lower
            or obj_lower in ("cube", "cubes", "box", "boxes", "all", "all objects", "table", "desk", "สิ่งของ", "กล่อง")
        )
    )


def _box_conf(box) -> float:
    try:
        return float(box.conf[0])
    except Exception:
        return 0.0


def _refine_name_hsv(frame, box, name: str) -> str:
    """HSV color refinement of a detected cube's class name.

    YOLO's class is kept when the crop actually contains that color (>= 60% of the HSV
    winner's pixels). A weakly-detected green cube (conf 0.3-0.4) under warm light has
    yellow-ish pixels too; overriding it on a mere majority made it invisible to green_cube
    queries. Below SCAN_TRUST_CONF the old behaviour (HSV majority wins) applies.
    """
    try:
        ih, iw = frame.shape[:2]
        bx_coords = box.xyxy[0].cpu().numpy()
        bx1, by1 = max(0, int(bx_coords[0])), max(0, int(bx_coords[1]))
        bx2, by2 = min(iw, int(bx_coords[2])), min(ih, int(bx_coords[3]))
        if bx2 > bx1 and by2 > by1:
            res = _hsv_color_counts(frame[by1:by2, bx1:bx2])
            verified_name = _dominant_color(*res) if res else None
            if verified_name and verified_name != name:
                counts = res[0]
                keep = 0.6 if _box_conf(box) >= getattr(armconfig, "SCAN_TRUST_CONF", 0.30) else 1.0
                if name in counts and counts[name] >= keep * counts[verified_name] and counts[name] >= 8:
                    print(f"🎨 <SYSTEM>: HSV เห็น {verified_name} แต่สี {name} ยังมีพิกเซลมากพอ → เชื่อ YOLO ({_box_conf(box):.2f})")
                    return name
                print(f"🎨 <SYSTEM>: ปรับปรุงสีด้วย HSV: {name} -> {verified_name}")
                return verified_name
    except Exception as e:
        print(f"⚠️ <SYSTEM>: HSV color verify failed: {e}")
    return name


def _box_to_world(box, j1: float, x_offset: float, y_offset: float) -> list:
    """Pixel box center -> arm base-frame [x, y] (rotated by the scan angle j1, offset, clamped)."""
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
    return [round(x_world, 2), round(y_world, 2)]


def _target_matches(obj_colors, obj_words, name_colors, name_words, name_lower) -> bool:
    """Targeted scan: does a detected class name match the requested object?"""
    if obj_colors:
        if not name_colors or not obj_colors.intersection(name_colors):
            return False
    return bool(obj_words.intersection(name_words) or any(w in name_lower for w in obj_words if len(w) > 2))


def _mem_z(coord) -> float:
    return float(coord[2]) if len(coord) >= 3 and coord[2] > 0 else armconfig.GRAB_BASE_HEIGHT


def _near_xy(a, b) -> bool:
    t = armconfig.STACK_PROXIMITY_THRESHOLD
    return abs(a[0] - b[0]) < t and abs(a[1] - b[1]) < t


def _placed_items(exclude: str = None):
    for k, v in init.known_objects.items():
        if k != exclude and isinstance(v, list) and len(v) >= 2 and "area" not in k.lower():
            yield k, v


def _estimate_z(name: str, coord: list) -> float:
    """Camera sees the top face only. Keep the remembered Z if the cube has not moved;
    otherwise sit it one layer above any remembered cube under the same XY."""
    old = init.known_objects.get(name)
    if isinstance(old, list) and len(old) >= 2 and math.hypot(coord[0] - old[0], coord[1] - old[1]) <= 15.0:
        return _mem_z(old)
    under = [_mem_z(v) for _, v in _placed_items(exclude=name) if _near_xy(v, coord)]
    return max(under) + armconfig.STACK_HEIGHT_PER_LAYER if under else armconfig.GRAB_BASE_HEIGHT


def _is_occluded(name: str, found_cubes: dict) -> bool:
    """A cube under a cube that the scan just saw cannot be seen from above — it is not gone."""
    v = init.known_objects.get(name)
    if not (isinstance(v, list) and len(v) >= 2):
        return False
    return any(k in found_cubes and _near_xy(w, v) and _mem_z(w) > _mem_z(v) + 10
               for k, w in _placed_items(exclude=name))


def _calibrate_memory(found_cubes: dict) -> None:
    """Full-desk scan: update moved cubes, add new ones, drop stale ones (keeping the held cube)."""
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
            if _is_occluded(old_k, found_cubes):
                print(f"🧱 <SYSTEM>: [Memory Check] '{old_k}' โดนกล่องอื่นทับ มองไม่เห็นจากด้านบน → เก็บไว้ในความจำ")
                continue
            print(f"🗑️ <SYSTEM>: [Memory Check] ไม่พบ '{old_k}' บนโต๊ะแล้ว → ลบออกจากความจำเพื่อความถูกต้อง 100%")
            init.known_objects.pop(old_k, None)


def _iter_detections(model, results, frame, primary_type, colors, j1, x_offset, y_offset):
    """Lazily yield (std_name, name_lower, name_words, name_colors, world_coord) per detected box."""
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            name = model.names[cls]

            # Non-invasive HSV color refinement for cube model
            if primary_type == "cube" and frame is not None:
                name = _refine_name_hsv(frame, box, name)

            name_lower = name.lower().replace("_", " ")
            name_words = set(name_lower.split())
            name_colors = name_words.intersection(colors)

            saved_coord = _box_to_world(box, j1, x_offset, y_offset)

            # Standardize cube key (e.g. "red_cube")
            std_name = name.lower()
            if "_" not in std_name and primary_type == "cube":
                std_name = f"{std_name}_cube"

            yield std_name, name_lower, name_words, name_colors, saved_coord


def _cast_vote(clusters: list, frame_idx: int, det: tuple) -> None:
    """Add one detection to the cluster of the same class within 25mm (max 1 vote per frame per cluster)."""
    std_name, name_lower, name_words, name_colors, coord = det
    for c in clusters:
        if c["name"] == std_name and math.hypot(c["x"] - coord[0], c["y"] - coord[1]) < 25.0:
            if c["last"] != frame_idx:
                c["votes"] += 1
                c["last"] = frame_idx
            c["xs"].append(coord[0])
            c["ys"].append(coord[1])
            c["x"], c["y"] = sum(c["xs"]) / len(c["xs"]), sum(c["ys"]) / len(c["ys"])
            return
    clusters.append({"name": std_name, "lower": name_lower, "words": name_words, "colors": name_colors,
                     "x": coord[0], "y": coord[1], "xs": [coord[0]], "ys": [coord[1]], "votes": 1, "last": frame_idx})


def _cluster_coord(c: dict) -> list:
    return [round(c["x"], 2), round(c["y"], 2)]


def _confirmed_target(clusters: list, need: int, obj_colors, obj_words):
    for c in clusters:
        if c["votes"] >= need and _target_matches(obj_colors, obj_words, c["colors"], c["words"], c["lower"]):
            return c
    return None


def _finish_targeted(c: dict, primary_type: str, j1: float) -> list:
    """Targeted scan hit: go home, remember the cube (with stack-aware Z), return [x, y]."""
    saved_coord = _cluster_coord(c)
    print(f"🤖 <SYSTEM>: YOLO ({primary_type}) เจอ '{c['name']}' ที่มุม {j1}! ({c['votes']} เฟรมยืนยัน) พิกัดโลก: {saved_coord}")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    init.known_objects[c["name"]] = [saved_coord[0], saved_coord[1], _estimate_z(c["name"], saved_coord)]
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    return saved_coord


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

    primary_type = _primary_type(name_lower)

    model = get_yolo_model(primary_type) or get_yolo_model("cube")
    if not model:
        return None

    from agent.tools.shares._raw import get_english_name
    eng_name = get_english_name(name_raw) if name_raw else ""
    obj_lower = eng_name.replace("_", " ").strip() if eng_name else name_lower

    # Determine if this is a general desk scan / memory calibration
    is_full_desk_scan = _is_full_desk_scan(primary_type, obj_lower)

    _announce_scan(is_full_desk_scan, name_raw, primary_type)

    scan_angles = armconfig.SCAN_ANGLES

    x_offset, y_offset = _load_xy_offsets()

    time.sleep(0.3)

    obj_words = set(obj_lower.split())
    colors = {'red', 'green', 'blue', 'yellow', 'orange'}
    obj_colors = obj_words.intersection(colors)

    found_cubes = {}
    conf_thresh = getattr(armconfig, "VISION_CONFIDENCE_THRESHOLD", 0.30)
    wait_time = getattr(armconfig, "SCAN_WAIT_PER_ANGLE", 1.5)
    frames_per_angle = max(1, int(getattr(armconfig, "SCAN_FRAMES_PER_ANGLE", 4)))
    min_votes = max(1, int(getattr(armconfig, "SCAN_MIN_VOTES", 2)))

    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO หันกล้องไปที่มุม {j1} องศา (ค้างรอ {wait_time}s)...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(wait_time)

        # Multi-frame voting: a weak detection (conf ~0.3-0.4) flickers frame to frame, so one
        # lucky/unlucky frame must not decide. Accept a box only after MIN_VOTES frames agree.
        clusters = []
        frames_got = 0
        for attempt in range(frames_per_angle):
            frame = cam_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            frames_got += 1

            results = model(frame, verbose=False, conf=conf_thresh)
            if hasattr(cam_manager, 'set_ai_results') and len(results) > 0:
                cam_manager.set_ai_results(results[0], duration=0.8)

            for det in _iter_detections(model, results, frame, primary_type, colors, j1, x_offset, y_offset):
                _cast_vote(clusters, attempt, det)

            # Targeted Scan Mode: return as soon as a matching box has MIN_VOTES frames
            if not is_full_desk_scan:
                hit = _confirmed_target(clusters, min_votes, obj_colors, obj_words)
                if hit:
                    return _finish_targeted(hit, primary_type, j1)

            time.sleep(0.1)

        # Camera delivered fewer frames than MIN_VOTES: accept what we could get rather than never detecting
        need = min(min_votes, max(frames_got, 1))

        if not is_full_desk_scan:
            hit = _confirmed_target(clusters, need, obj_colors, obj_words)
            if hit:
                return _finish_targeted(hit, primary_type, j1)

        # Full Desk Scan Mode: aggregate every box that was confirmed by enough frames
        if is_full_desk_scan:
            for c in clusters:
                if c["votes"] >= need:
                    found_cubes[c["name"]] = _cluster_coord(c)
                else:
                    print(f"🤔 <SYSTEM>: '{c['name']}' เห็นแค่ {c['votes']}/{frames_got} เฟรม → ยังไม่นับ (กันตรวจผิดชั่วคราว)")

    # ── Post-Scan Processing ───────────────────────────────────────────────────
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(0.5)

    # Full Desk Scan: Re-calibrate memory 100%
    if is_full_desk_scan:
        _calibrate_memory(found_cubes)

        print(f"✅ <SYSTEM>: [Central Scanner] สแกนครบถ้วน ความจำสมบูรณ์ 100%: {init.known_objects}")
        return init.known_objects

    print(f"🤖 <SYSTEM>: YOLO สแกนครบ {len(scan_angles)} มุมแล้ว ไม่พบ '{name_raw}'")
    return None


# Centralized alias for direct memory calibration calls
def verify_and_calibrate_memory() -> dict:
    """Re-scan entire desk and re-calibrate known_objects memory 100%. Returns updated known_objects dict."""
    return scan_with_yolo("cube")
