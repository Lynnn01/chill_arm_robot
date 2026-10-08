"""
agent/tools/_raw.py — Raw (unwrapped) tool functions for executor.py

These are the actual Python logic functions without the @function_tool decorator,
so executor.py can call them directly without going through openai-agents async machinery.
"""

import time
import json
import math
import os
import csv
from hardware.init import mc
from hardware import init
import armconfig

# สีของวัตถุที่รู้จัก — ใช้ตรวจ alias cleanup
_OBJECT_COLORS = frozenset({"red", "green", "blue", "yellow", "orange", "purple", "pink", "white", "black"})


def _find_in_memory(eng_name: str) -> tuple:
    """
    Find matching object in init.known_objects with strict color enforcement.
    Returns: (found_key, coord) or (None, None)
    """
    if not eng_name:
        return None, None
    
    # 1. Exact match
    if eng_name in init.known_objects and isinstance(init.known_objects[eng_name], list) and init.known_objects[eng_name] != "in gripper":
        return eng_name, init.known_objects[eng_name]
        
    target_color = next((c for c in _OBJECT_COLORS if c in eng_name.lower()), None)
    
    # 2. Strict color-aware fuzzy match
    for k, v in init.known_objects.items():
        if not isinstance(v, list) or v == "in gripper" or "area" in k.lower():
            continue
        k_color = next((c for c in _OBJECT_COLORS if c in k.lower()), None)
        
        if target_color:
            # Target has a color (e.g. yellow): MUST only match keys with same color!
            if k_color == target_color:
                return k, v
        else:
            # Target is generic (no color): can match generic or any cube
            if eng_name.lower() in k.lower() or k.lower() in eng_name.lower():
                return k, v
                
    return None, None


def _drop_gripper_aliases(keep: str = None) -> None:
    """After release the gripper is empty, so no other memory key may stay 'in gripper'."""
    for k in [k for k, v in init.known_objects.items() if v == "in gripper" and k != keep]:
        init.known_objects.pop(k, None)


def _is_placed(name: str, coord) -> bool:
    """Remembered object with a real [x, y, ...] coordinate (not in gripper, not an 'area')."""
    return isinstance(coord, list) and len(coord) >= 2 and coord != "in gripper" and "area" not in name.lower()


def _coord_z(coord: list) -> float:
    return float(coord[2]) if len(coord) >= 3 and coord[2] > 0 else armconfig.GRAB_BASE_HEIGHT


def _is_near_xy(coord: list, x: float, y: float) -> bool:
    """Within the stacking proximity threshold in both X and Y."""
    return abs(coord[0] - x) < armconfig.STACK_PROXIMITY_THRESHOLD and abs(coord[1] - y) < armconfig.STACK_PROXIMITY_THRESHOLD


def _put_down_held(message_template: str):
    """If the gripper holds something, place it at a safe spot first. Returns an ERROR dict or None.

    message_template is printed with {held} filled in."""
    if not (init.is_holding_object or init.current_held_object):
        return None
    held = init.current_held_object or "held_object"
    print("⚠️ <SYSTEM>: " + message_template.format(held=held))
    safe_spot = raw_find_safe_spot()
    res = raw_move_to(target_coord=safe_spot)
    if isinstance(res, dict) and res.get("status") == "ERROR":
        return {"status": "ERROR", "message": f"วาง '{held}' ลงตำแหน่งปลอดภัยไม่สำเร็จ! {res.get('message', '')}"}
    return None


def _highest_object_at(target_coord: list, is_stack_intent: bool):
    """(z, name) of the tallest remembered object under target_coord, or (None, None)."""
    max_z_at_xy = None
    stack_target_name = None
    for obj_name, coord in init.known_objects.items():
        if isinstance(coord, list) and len(coord) >= 2 and coord != "in gripper":
            if "area" in obj_name.lower() or "พื้นที่" in obj_name or "zone" in obj_name.lower():
                continue
            if obj_name == init.current_held_object:
                continue

            dx = abs(coord[0] - target_coord[0])
            dy = abs(coord[1] - target_coord[1])
            # ถ้าตั้งใจวางซ้อน หรือพิกัดตรงกับกล่องอื่นจริงๆ (< 25mm)
            if (is_stack_intent and dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD) or (dx < 25.0 and dy < 25.0):
                obj_z = float(coord[2]) if len(coord) >= 3 and float(coord[2]) > 0 else armconfig.STACK_BASE_HEIGHT
                if max_z_at_xy is None or obj_z > max_z_at_xy:
                    max_z_at_xy = obj_z
                    stack_target_name = obj_name
    return max_z_at_xy, stack_target_name


def _scan_unstack_target(eng_name: str, object_name: str):
    """Memory miss during unstack: scan with YOLO and remember the result."""
    from vision import yolo_detector
    print(f"🤖 <SYSTEM>: [Unstack] ไม่พบ '{eng_name}' ในความจำ → สแกนหาด้วยกล้อง...")
    target_coord = yolo_detector.scan_with_yolo(eng_name or object_name)
    if target_coord:
        init.known_objects[eng_name] = target_coord
    return target_coord


# ── grab_object ──────────────────────────────────────────────────────────────────

def _is_cube_query(eng_name: str, object_name: str) -> bool:
    """Colored cube/block queries must never fall back to QwenVL (prevents hallucinated boxes)."""
    return any(c in eng_name.lower() for c in _OBJECT_COLORS) or "cube" in eng_name.lower() or "block" in eng_name.lower() or "กล่อง" in object_name or "บล็อก" in object_name


def _vision_locate(eng_name: str, object_name: str, x_offset: float, y_offset: float):
    """QwenVL fallback. Returns robot [x, y] or None. Result is NOT saved to memory."""
    from vision import eyeonhand, api
    from PIL import Image

    print(f"🤖 <SYSTEM>: YOLO สแกนไม่พบ → กำลังใช้กล้อง Vision AI (QwenVL) ค้นหา '{eng_name}'...")
    init.GetImage()
    img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
    width, height = Image.open(img_path).size
    positions = api.QwenVLRequest("a " + eng_name, img_path).get("coordinates", [])
    if not positions:
        print(f"🤖 <SYSTEM>: ไม่พบ {object_name} ในภาพ")
        return None
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
    # catlazy: QwenVL result used for THIS grab only — NOT saved to memory (prevents hallucinated coords)
    print(f"🤖 <SYSTEM>: Vision เจอแล้ว! พิกัด {robot_coord}")
    return robot_coord


def _scan_and_locate(object_name: str, eng_name: str, z: float, x_offset: float, y_offset: float):
    """Memory miss: YOLO scan, then QwenVL for non-cube queries. Returns (robot_coord, err_dict)."""
    from vision import yolo_detector

    print(f"🤖 <SYSTEM>: ไม่พบ '{eng_name}' ในความจำ → เริ่มสแกนค้นหาด้วย YOLO...")
    yolo_coord = yolo_detector.scan_with_yolo(eng_name)
    if yolo_coord:
        robot_coord = yolo_coord
        # scan_with_yolo บันทึก Z ที่ประเมินจากกองกล่องไว้แล้ว — ใช้ค่านั้นแทน base เพื่อไม่ให้ดิ่งชนกอง
        _, saved = _find_in_memory(eng_name)
        if saved and abs(saved[0] - robot_coord[0]) < 1.0 and abs(saved[1] - robot_coord[1]) < 1.0:
            z = _coord_z(saved)
        init.known_objects[eng_name] = [round(robot_coord[0], 2), round(robot_coord[1], 2), round(z, 2)]
        print(f"🤖 <SYSTEM>: YOLO เจอแล้วที่ {robot_coord} และบันทึกลงความจำ")
        return robot_coord, None

    # If target is a colored cube/block and YOLO didn't find it -> Report not found immediately!
    # Do NOT call QwenVL for colored cubes to prevent hallucinated false box positions.
    if _is_cube_query(eng_name, object_name):
        print(f"🤖 <SYSTEM>: YOLO สแกนโต๊ะครบทุกมุมแล้ว ไม่พบ '{object_name}' จริงๆ")
        init.known_objects.pop(eng_name, None)
        return None, {"status": "ERROR", "message": f"ไม่พบ {object_name} บนโต๊ะ (สแกนตรวจหาแล้วไม่มีอยู่จริง)"}

    robot_coord = _vision_locate(eng_name, object_name, x_offset, y_offset)
    if robot_coord is None:
        return None, {"status": "ERROR", "message": f"ไม่พบ {object_name} ในภาพ"}
    return robot_coord, None


def _resolve_grab_target(object_name, eng_name, target_coord, z, x_offset, y_offset):
    """Returns (robot_coord, z, eng_name, err). err is an ERROR dict or None."""
    if target_coord and len(target_coord) >= 2:
        print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปหยิบของที่พิกัด {target_coord}...")
        robot_coord = [float(target_coord[0]), float(target_coord[1])]
        if len(target_coord) >= 3 and float(target_coord[2]) > 0:
            z = float(target_coord[2])
        return robot_coord, z, eng_name, None

    # 1. MEMORY FIRST: Check known_objects with strict color matching
    found_key, saved = _find_in_memory(eng_name)
    if found_key and saved:
        robot_coord = [float(saved[0]), float(saved[1])]
        if len(saved) >= 3 and float(saved[2]) > 0:
            z = float(saved[2])
        print(f"🤖 <SYSTEM>: [Memory-First] ดึงพิกัด '{found_key}' จากความจำ (X={robot_coord[0]}, Y={robot_coord[1]}, Z={z}) (เริ่มจากความทรงจำก่อน ข้ามการสแกน)...")
        return robot_coord, z, found_key, None

    # 2. SCAN IF NOT IN MEMORY
    robot_coord, err = _scan_and_locate(object_name, eng_name, z, x_offset, y_offset)
    if robot_coord and isinstance(init.known_objects.get(eng_name), list):
        z = _coord_z(init.known_objects[eng_name])
    return robot_coord, z, eng_name, err


def _is_buried(eng_name: str, robot_coord: list, z: float) -> bool:
    """True if another remembered object sits above the target (needs unstacking first)."""
    tx, ty = robot_coord[0], robot_coord[1]
    for k, v in init.known_objects.items():
        if isinstance(v, list) and len(v) >= 2 and k != eng_name and "area" not in k.lower() and v != "in gripper":
            dx, dy = abs(v[0] - tx), abs(v[1] - ty)
            if dx < armconfig.STACK_PROXIMITY_THRESHOLD and dy < armconfig.STACK_PROXIMITY_THRESHOLD:
                vz = float(v[2]) if len(v) >= 3 and v[2] > 0 else armconfig.GRAB_BASE_HEIGHT
                if vz > z + 10:
                    print(f"⚠️ <SYSTEM>: ตรวจพบวัตถุ '{k}' (Z={vz}) ทับอยู่บน '{eng_name}' (Z={z})! เปลี่ยนไปใช้กระบวนการแกะกล่อง (unstack) อัตโนมัติ...")
                    return True
    return False


def _clamp_grab_coord(robot_coord: list) -> None:
    """In-place: keep XY out of the base singularity radius and inside workspace bounds."""
    radius = math.hypot(robot_coord[0], robot_coord[1])
    min_r = getattr(armconfig, "GRAB_MIN_RADIUS", 150.0)
    if radius < min_r and radius > 0:
        scale = min_r / radius
        robot_coord[0] *= scale
        robot_coord[1] *= scale
        print(f"🤖 <SYSTEM>: ปรับพิกัดรัศมีจาก {radius:.1f}mm เป็น {min_r}mm ป้องกันข้อต่อติดขัดใกล้ฐาน")

    robot_coord[0] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[0]))
    robot_coord[1] = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, robot_coord[1]))


def _resolve_grabbed_name(eng_name: str, robot_coord: list) -> str:
    """ถ้าชื่อที่หยิบเป็น generic (ไม่มีสี) ให้ค้นหาชื่อจริงจาก known_objects ที่ชี้พิกัดเดียวกัน"""
    if any(c in eng_name.lower() for c in _OBJECT_COLORS):
        return eng_name
    for k, v in init.known_objects.items():
        if k == eng_name or not isinstance(v, list) or len(v) < 2:
            continue
        if any(c in k.lower() for c in _OBJECT_COLORS):
            if abs(v[0] - robot_coord[0]) < 15.0 and abs(v[1] - robot_coord[1]) < 15.0:
                print(f"🤖 <SYSTEM>: แก้ชื่อจาก '{eng_name}' → '{k}' (เจอชื่อจริงได้จากความจำ)")
                return k
    return eng_name


def _record_grabbed(eng_name: str, robot_coord: list, z: float) -> None:
    """Update memory after a successful grab: fix generic name, mark held + same-spot aliases."""
    eng_name = _resolve_grabbed_name(eng_name, robot_coord)

    init.current_held_object = eng_name
    init.current_held_coord = [robot_coord[0], robot_coord[1]]
    init.known_objects[eng_name] = "in gripper"
    _mark_aliases_in_gripper(eng_name, robot_coord, z)


def _mark_aliases_in_gripper(eng_name: str, robot_coord: list, z: float) -> None:
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



def _log_motion(row: dict) -> None:
    """Append one row to the motion CSV (commanded vs actual position, grip value...). Never raises."""
    path = getattr(armconfig, "MOTION_LOG", "")
    if not path:
        return
    try:
        full = path if os.path.isabs(path) else os.path.join(init.PROJECT_ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        fields = ["time", "action", "name", "tx", "ty", "tz", "ax", "ay", "az", "err_x", "err_y",
                  "corrected", "grip", "result"]
        new = not os.path.exists(full)
        with open(full, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow({"time": time.strftime("%Y-%m-%d %H:%M:%S"), **row})
    except Exception as e:
        print(f"⚠️ <SYSTEM>: เขียน motion log ไม่ได้: {e}")


def _read_xyz():
    """Real [x, y, z] from the arm, or None (no reading / mock / garbage)."""
    try:
        c = mc.safe_get_coords()
    except Exception:
        return None
    if isinstance(c, (list, tuple)) and len(c) >= 3 and all(isinstance(v, (int, float)) for v in c[:3]):
        return [float(c[0]), float(c[1]), float(c[2])]
    return None


def _verify_xy(target: list, wrist: list, action: str, name: str = "") -> dict:
    """Closed-loop check after reaching Z: compare the real XY with the commanded one and fix once.

    wait_for_z only watches Z, so a head that stopped short in X (arm reach / droop) used to
    close the gripper off-center. Reads beyond XY_FIX_MAX are treated as stale/mock and only logged."""
    tol = getattr(armconfig, "XY_TOLERANCE", 4.0)
    fix_max = getattr(armconfig, "XY_FIX_MAX", 40.0)
    actual = _read_xyz()
    row = {"action": action, "name": name, "tx": round(target[0], 1), "ty": round(target[1], 1),
           "tz": round(target[2], 1), "corrected": 0}
    if actual is None:
        _log_motion({**row, "result": "no_reading"})
        return {"actual": None, "err": None, "corrected": False}

    err = (actual[0] - target[0], actual[1] - target[1])
    dist = math.hypot(*err)
    corrected = False
    if tol < dist <= fix_max:
        print(f"🎯 <SYSTEM>: [{action}] XY คลาด {dist:.1f}mm (X {err[0]:+.1f}, Y {err[1]:+.1f}) → สั่งแก้ซ้ำ")
        mc.send_coords(list(target) + list(wrist), armconfig.SPEED_DESCEND)
        mc.wait_for_arrival(list(target), timeout=3.0, threshold=6.0)
        again = _read_xyz()
        if again is not None:
            actual = again
            err = (actual[0] - target[0], actual[1] - target[1])
            dist = math.hypot(*err)
        corrected = True
    elif dist > fix_max:
        print(f"⚠️ <SYSTEM>: [{action}] ค่าตำแหน่งจริงต่างจากเป้า {dist:.0f}mm — น่าจะอ่านค่าผิด ไม่แก้")
    else:
        print(f"🎯 <SYSTEM>: [{action}] XY ตรงเป้า (คลาด {dist:.1f}mm)")
    _log_motion({**row, "ax": round(actual[0], 1), "ay": round(actual[1], 1), "az": round(actual[2], 1),
                 "err_x": round(err[0], 1), "err_y": round(err[1], 1), "corrected": int(corrected),
                 "result": "ok" if dist <= tol else "off"})
    return {"actual": actual, "err": err, "corrected": corrected}


def _retreat_home(above: list) -> None:
    """Abort path: rise straight up first (never sweep sideways at low Z), then go home."""
    mc.send_coords(above + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(above, mode="coords")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")


def raw_grab_object(object_name: str, target_coord: list = None, _auto_unstack: bool = True) -> list:
    """Grab an object. Returns [x, y] robot coord.

    A missed grab (gripper closed on air, needs GRIP_EMPTY_MAX) forgets the stale coordinate,
    re-scans the desk and tries again up to GRAB_RETRIES times."""
    result = _grab_attempt(object_name, target_coord, _auto_unstack, first=True)
    retries = getattr(armconfig, "GRAB_RETRIES", 1)
    for n in range(1, retries + 1):
        if not (isinstance(result, dict) and result.get("status") == "ERROR"
                and str(result.get("message", "")).startswith("Missed grab")):
            break
        print(f"🔁 <SYSTEM>: หยิบพลาด → สแกนหา '{object_name}' ใหม่แล้วลองอีกครั้ง ({n}/{retries})")
        # target_coord=None: the caller's coordinate is the one that just missed
        result = _grab_attempt(object_name, None, _auto_unstack, first=False)
    return result


def _grab_attempt(object_name: str, target_coord, _auto_unstack: bool, first: bool):
    err = _put_down_held("กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อนแล้วค่อยหยิบใหม่...")
    if err:
        return err

    if first:
        init.BotInit(mc)

    with open(init.CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    x_offset = cfg.get("x", 0)
    y_offset = cfg.get("y", 0)
    z_offset = cfg.get("z", 0)
    z = armconfig.GRAB_BASE_HEIGHT + z_offset
    eng_name = get_english_name(object_name)

    robot_coord, z, eng_name, err = _resolve_grab_target(object_name, eng_name, target_coord, z, x_offset, y_offset)
    if err:
        return err

    # SAFETY: Auto-detect buried objects and unstack them!
    if _auto_unstack and not target_coord and _is_buried(eng_name, robot_coord, z):
        return raw_unstack_and_grab(object_name)

    _clamp_grab_coord(robot_coord)
    z = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX - armconfig.Z_CLEARANCE, z))
    # เข้าหาจากเหนือยอดกองเสมอ — กล่องชั้นบนของหอคอยสูงอาจอยู่ที่ระดับ Z_SAFE_TRAVEL พอดี
    above = [robot_coord[0], robot_coord[1], max(armconfig.Z_SAFE_TRAVEL, z + armconfig.Z_CLEARANCE)]
    at_z = [robot_coord[0], robot_coord[1], z]

    init.open_gripper()
    mc.send_coords(above + armconfig.WRIST_DOWN, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(above, mode="coords")
    time.sleep(0.5)  # พักเคลียร์บอร์ดให้พร้อมรับคำสั่งดำดิ่งถัดไป

    print(f"🤖 <SYSTEM>: กำลังพุ่งหัวลงไปหยิบที่ Z={z}...")
    mc.send_coords(at_z + armconfig.WRIST_DOWN, armconfig.SPEED_DESCEND)
    time.sleep(0.2)
    mc.send_coords(at_z + armconfig.WRIST_DOWN, armconfig.SPEED_DESCEND)  # ส่งคำสั่งย้ำป้องกันเฟิร์มแวร์เมิน
    reached_z = mc.wait_for_z(z)   # รอเฉพาะแกน Z — ไม่สนใจ XY drift

    if not reached_z:
        print(f"⚠️ <SYSTEM>: ไม่สามารถลงไปถึงระดับหยิบ Z={z} ได้! ดึงหัวกลับตำแหน่งปลอดภัยและยกเลิกภารกิจ")
        _retreat_home(above)
        return {"status": "ERROR", "message": f"Joint stall at target Z={z}. Object unreachable."}

    mc.wait_for_arrival(at_z, timeout=2.0, threshold=12.0)  # รอ XY นิ่งก่อนหนีบ
    xy = _verify_xy(at_z, armconfig.WRIST_DOWN, "grab", eng_name)  # XY จริงตรงเป้าไหม — แก้ซ้ำถ้าคลาด
    time.sleep(0.3)
    grip_val = init.close_gripper()
    time.sleep(1.2)  # รอกริปเปอร์หนีบเสร็จสนิท
    _log_motion({"action": "grab_close", "name": eng_name, "tx": round(at_z[0], 1), "ty": round(at_z[1], 1),
                 "tz": round(z, 1), "grip": grip_val, "corrected": int(bool(xy["corrected"])),
                 "result": "closed"})

    if armconfig.GRIP_EMPTY_MAX >= 0 and isinstance(grip_val, (int, float)) and grip_val <= armconfig.GRIP_EMPTY_MAX:
        print(f"⚠️ <SYSTEM>: หนีบไม่โดน '{eng_name}' (ค่ากริปเปอร์ {grip_val}) → ล้างพิกัดในความจำให้สแกนใหม่รอบหน้า")
        init.open_gripper()
        init.known_objects.pop(eng_name, None)
        _retreat_home(above)
        return {"status": "ERROR", "message": f"Missed grab: {object_name} not in gripper (value={grip_val}). Scan again."}

    _record_grabbed(eng_name, robot_coord, z)

    mc.send_coords(above + armconfig.WRIST_DOWN, armconfig.SPEED_LIFT)
    mc.wait_for_arrival(above, mode="coords")

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

# ── find_safe_spot & smart_place ──────────────────────────────────────────────

# ── find_safe_spot & smart_place ──────────────────────────────────────────────

def _collect_obstacles() -> list:
    """(name, x, y) of every remembered object plus the held object's pickup spot."""
    obstacles = []
    for k, v in init.known_objects.items():
        if isinstance(v, list) and len(v) >= 2 and v != "in gripper" and "area" not in k.lower():
            obstacles.append((k, float(v[0]), float(v[1])))

    # Also treat current held object's pickup coord as an obstacle so we don't drop right back
    if hasattr(init, "current_held_coord") and init.current_held_coord:
        obstacles.append(("held_origin", float(init.current_held_coord[0]), float(init.current_held_coord[1])))
    return obstacles


def _sample_free_spot(obstacles: list, margin_mm: float):
    """Random search (80 tries) for a reachable [x, y] at least margin_mm from every obstacle."""
    import random
    # Workspace reachable zone on table: X: 130 to 220, Y: -150 to 150
    for attempt in range(80):
        x = random.uniform(130.0, 220.0)
        y = random.uniform(-150.0, 150.0)
        dist_base = math.hypot(x, y)
        if dist_base < armconfig.GRAB_MIN_RADIUS or dist_base > 255.0:
            continue
        if all(math.hypot(x - ox, y - oy) >= margin_mm for _, ox, oy in obstacles):
            return [round(x, 1), round(y, 1)]
    return None


def _max_clearance_spot(obstacles: list):
    """Crowded desk fallback: best of 50 random points by distance to nearest obstacle."""
    import random
    best_spot = [armconfig.UNSTACK_SAFE_X, armconfig.UNSTACK_SAFE_Y]
    max_min_dist = -1.0
    for _ in range(50):
        x = random.uniform(130.0, 220.0)
        y = random.uniform(-150.0, 150.0)
        if math.hypot(x, y) < armconfig.GRAB_MIN_RADIUS:
            continue
        if not obstacles:
            return [round(x, 1), round(y, 1)], None
        min_d = min(math.hypot(x - ox, y - oy) for _, ox, oy in obstacles)
        if min_d > max_min_dist:
            max_min_dist = min_d
            best_spot = [round(x, 1), round(y, 1)]
    return best_spot, max_min_dist


def raw_find_safe_spot(margin_mm: float = 55.0, scan_first: bool = False) -> list:
    """
    Find a verified safe [x, y] spot on the table where NO boxes or obstacles exist.
    Checks memory (known_objects) first. Only scans table if memory is empty or scan_first=True.
    """
    # 1. Memory First: Scan desk only if memory is completely empty or scan_first=True
    has_valid_memory = any(isinstance(v, list) and v != "in gripper" for v in init.known_objects.values())
    if scan_first or not has_valid_memory:
        try:
            from vision.yolo_detector import scan_with_yolo
            scan_with_yolo("cube")
        except Exception as e:
            print(f"⚠️ <SYSTEM>: ไม่สามารถสแกนกล้องสดได้: {e} (ใช้ความจำ known_objects แทน)")

    # 2. Collect all active obstacles on desk
    obstacles = _collect_obstacles()

    print(f"🤖 <SYSTEM>: [Safety Check] กำลังค้นหาพื้นที่ว่าง (ระยะห่างจากกล่องทุกใบอย่างน้อย {margin_mm}mm, ตรวจเทียบกับสิ่งกีดขวาง {len(obstacles)} จุด)...")

    # 3. Generate and verify candidate locations
    spot = _sample_free_spot(obstacles, margin_mm)
    if spot:
        print(f"✅ <SYSTEM>: [Safety Check] พบพื้นที่ปลอดภัยที่ว่าง ไม่มีกล่องอยู่ใกล้เคียงที่ {spot}")
        return spot

    # 4. Fallback if desk is crowded: Find the spot with the maximum clearance from all obstacles
    print(f"⚠️ <SYSTEM>: [Safety Check] โต๊ะมีกล่องค่อนข้างแน่น กำลังคำนวณหาจุดที่มีระยะห่างจากกล่องอื่นมากที่สุด...")
    best_spot, max_min_dist = _max_clearance_spot(obstacles)
    if max_min_dist is not None:
        print(f"🤖 <SYSTEM>: [Safety Check] เลือกจุดที่โล่งที่สุดที่พิกัด {best_spot} (ระยะห่าง {max_min_dist:.1f}mm)")
    return best_spot


def raw_smart_place(prefer_stack: bool = True) -> dict:
    """
    Autonomously place the currently held object:
    - If prefer_stack=True and other objects exist in memory -> Stack on one of them
    - If no objects to stack on or prefer_stack=False -> Find a verified safe empty spot
    """
    if not init.current_held_object and not init.is_holding_object:
        print(f"⚠️ <SYSTEM>: กริปเปอร์ไม่ได้ถือวัตถุอยู่! ยกเลิก smart_place")
        return {"status": "ERROR", "message": "No object held in gripper. Call grab_object first."}

    held = init.current_held_object or "held_object"
    held_coord = getattr(init, "current_held_coord", None)

    if prefer_stack:
        # Find candidate objects to stack on
        candidates = []
        for k, v in init.known_objects.items():
            if (
                isinstance(v, list)
                and len(v) >= 2
                and v != "in gripper"
                and k != held
                and "area" not in k.lower()
            ):
                # Don't stack on same spot where it was just picked up from
                if held_coord and abs(v[0] - held_coord[0]) < 35.0 and abs(v[1] - held_coord[1]) < 35.0:
                    continue
                candidates.append((k, v))

        if candidates:
            import random
            target_name, target_coord = random.choice(candidates)
            print(f"🤖 <SYSTEM>: [Smart Place] เลือกวางซ้อนบน '{target_name}' ที่พิกัด {target_coord[:2]}")
            return raw_move_to(target_coord=target_coord[:2], target_name=target_name)

    # Fallback / Direct: Find a verified safe empty spot (Memory First)
    spot = raw_find_safe_spot()
    print(f"🤖 <SYSTEM>: [Smart Place] พบพื้นที่ว่างที่ปลอดภัยที่ {spot}")
    return raw_move_to(target_coord=spot)


_SMART_PLACE_TERMS = ("smart", "auto", "random", "stack", "safe", "any", "table", "พื้นที่ว่าง")
_STACK_INTENT_TERMS = ("cube", "block", "stack", "กล่อง", "บล็อก", "ซ้อน", "red", "green", "blue", "yellow", "แดง", "เขียว", "น้ำเงิน", "เหลือง")


def _wants_smart_place(smart_place: bool, target_name, target_coord) -> bool:
    return bool(smart_place or (target_name and any(term in target_name.lower() for term in _SMART_PLACE_TERMS) and not target_coord))


def _is_invalid_target(target_coord, target_name) -> bool:
    """Default [0,0], empty, the pickup spot of the held object, or an 'area' name -> must re-resolve."""
    is_held_coord = False
    if hasattr(init, "current_held_coord") and init.current_held_coord and target_coord and isinstance(target_coord, list) and len(target_coord) >= 2:
        dx = abs(target_coord[0] - init.current_held_coord[0])
        dy = abs(target_coord[1] - init.current_held_coord[1])
        if dx < 35.0 and dy < 35.0:
            is_held_coord = True
            print(f"⚠️ <SYSTEM>: target_coord {target_coord} ตรงกับตำแหน่งเดิมของวัตถุที่ถืออยู่! ยกเลิกการใช้พิกัดซ้ำ")

    return bool(
        not target_coord or
        target_coord in ([0, 0], [0, 0, 0], [0.0, 0.0], [0.0, 0.0, 0.0]) or
        (isinstance(target_coord, list) and len(target_coord) >= 2 and target_coord[0] == 0 and target_coord[1] == 0) or
        is_held_coord or
        (target_name and "area" in target_name.lower())
    )


def _resolve_named_target(target_name: str):
    """Memory first, then YOLO scan (not for areas), else a safe spot."""
    eng_name = get_english_name(target_name)

    # 1. MEMORY FIRST: Check matching key in init.known_objects memory with strict color matching
    found_key, target_coord = _find_in_memory(eng_name)

    if found_key and target_coord:
        print(f"🤖 <SYSTEM>: [Memory-First] ใช้พิกัดของ '{found_key}' จากความจำ {target_coord}")
        return target_coord

    # 2. SCAN IF NOT IN MEMORY
    if "area" not in eng_name.lower():
        from vision import yolo_detector
        found_coord = yolo_detector.scan_with_yolo(eng_name)
        if found_coord:
            target_coord = found_coord

    if not target_coord:
        print(f"⚠️ <SYSTEM>: ไม่พบเป้าหมาย '{eng_name}' → สลับไปหาตำแหน่งที่ปลอดภัยเพื่อวางแทน")
        target_coord = raw_find_safe_spot()
    return target_coord


def _placement_height(target_coord: list, target_name) -> float:
    """Z for placing: on top of any object under the target (stack) or the table base height."""
    # Stacking detection: only when target_name indicates an object/stack or target_coord is directly over an object
    is_stack_intent = bool(target_name and any(term in target_name.lower() for term in _STACK_INTENT_TERMS))
    max_z_at_xy, stack_target_name = _highest_object_at(target_coord, is_stack_intent)

    if max_z_at_xy is not None:
        # วางซ้อนบนวัตถุเดิม: Z = ความสูงวัตถุเดิม + STACK_HEIGHT_PER_LAYER
        target_height = max_z_at_xy + armconfig.STACK_HEIGHT_PER_LAYER + getattr(armconfig, "STACK_SAFE_OFFSET", 0.0)
        print(f"🤖 <SYSTEM>: [Stack Placement] ตรวจพบวัตถุ '{stack_target_name}' (Z={max_z_at_xy}) → วางซ้อนที่ระดับ Z={target_height}")
    else:
        # วางลงบนพื้นโต๊ะโดยตรง: ใช้ระดับ STACK_BASE_HEIGHT (110)
        target_height = armconfig.STACK_BASE_HEIGHT
        print(f"🤖 <SYSTEM>: [Ground Placement] วางลงบนพื้นโต๊ะที่ระดับ Z={target_height}")
    return target_height


def raw_move_to(target_coord: list = None, target_name: str = None, target_height: int = None, smart_place: bool = False) -> dict:
    """Move and place current object at target_coord, on top of target_name, or smart place."""
    if not init.current_held_object and not init.is_holding_object:
        print(f"⚠️ <SYSTEM>: กริปเปอร์ไม่ได้ถือวัตถุอยู่! ยกเลิก move_to เพื่อป้องกันแขนกลขยับเปล่า (ต้องสั่ง grab_object ก่อน)")
        return {"status": "ERROR", "message": "No object held in gripper. Call grab_object first."}

    held_obj_name = init.current_held_object or "held_object"

    # If explicit smart_place requested or generic target without specific coords
    if _wants_smart_place(smart_place, target_name, target_coord):
        prefer_stack = not (target_name and "random" in target_name.lower())
        return raw_smart_place(prefer_stack=prefer_stack)

    if _is_invalid_target(target_coord, target_name) and target_name:
        target_coord = _resolve_named_target(target_name)

    if not target_coord or (isinstance(target_coord, list) and len(target_coord) >= 2 and target_coord[0] == 0 and target_coord[1] == 0):
        print(f"⚠️ <SYSTEM>: ไม่ได้ระบุพิกัดเป้าหมาย → หาตำแหน่งที่ปลอดภัยเพื่อวาง")
        target_coord = raw_find_safe_spot()

    # 3. ACCURATE HEIGHT CALCULATION FOR PLACEMENT & STACKING
    if target_height is None:
        target_height = _placement_height(target_coord, target_name)

    tc = [max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[0]) + armconfig.STACK_X_OFFSET)),
          max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[1]) + armconfig.STACK_Y_OFFSET))]
    th = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, int(target_height)))

    # Dynamic approach and retreat heights based on actual target height
    z_approach = min(armconfig.COORD_Z_MAX, max(armconfig.Z_PRE_PLACE, th + armconfig.Z_CLEARANCE))
    z_retreat = min(armconfig.COORD_Z_MAX, max(armconfig.Z_SAFE_TRAVEL, th + 50))

    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่พิกัด {tc} ความสูง {th} (เข้าประชิดที่ Z={z_approach})...")
    mc.send_coords([tc[0], tc[1], z_approach] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival([tc[0], tc[1], z_approach], mode="coords")
    time.sleep(0.3)

    print(f"🤖 <SYSTEM>: กำลังลดระดับหัวลงวางที่ Z={th}...")
    mc.send_coords([tc[0], tc[1], th] + armconfig.WRIST_PLACE, armconfig.SPEED_DESCEND)
    time.sleep(0.2)
    mc.send_coords([tc[0], tc[1], th] + armconfig.WRIST_PLACE, armconfig.SPEED_DESCEND)
    mc.wait_for_z(th)
    mc.wait_for_arrival([tc[0], tc[1], th], timeout=2.0, threshold=12.0)  # รอ XY นิ่งก่อนปล่อย
    _verify_xy([tc[0], tc[1], th], armconfig.WRIST_PLACE, "place", held_obj_name)
    time.sleep(0.3)  # รอให้นิ่งสนิทที่ระดับพิกัดเป้าหมายจริงก่อนเปิดกริปเปอร์
    init.open_gripper()
    time.sleep(1.0)

    print(f"🤖 <SYSTEM>: ถอยหัวกลับแนวตั้งถึงระดับปลอดภัย Z={z_retreat} ป้องกันการสะบัดโดนของ...")
    mc.send_coords([tc[0], tc[1], z_retreat] + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival([tc[0], tc[1], z_retreat], mode="coords")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")

    # บันทึกพิกัดในเฟรมเดียวกับกล้อง/ความจำ (ก่อนบวก STACK offset) — ถ้าเก็บ tc
    # การวางซ้อนชั้นถัดไปจะบวก offset ซ้ำ ทำให้หอคอยเอียงสะสมชั้นละ STACK_*_OFFSET
    mem_x = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[0])))
    mem_y = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(target_coord[1])))
    init.known_objects[held_obj_name] = [round(mem_x, 2), round(mem_y, 2), round(th, 2)]
    _drop_gripper_aliases(held_obj_name)
    init.current_held_object = None
    init.is_holding_object = False

    print(f"✅ <SYSTEM>: DONE TASK - Placed at {tc} (Z={th})")
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
    err = _put_down_held("กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อน...")
    if err:
        return err

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
    err = _put_down_held("กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อนเต้น...")
    if err:
        return err

    print("Dancing! 💃 (Upright Victory Dance)")
    speed = armconfig.SPEED_DANCE
    # 1. ยกแขนขึ้นตั้งตรงระดับสูงสุด (POSE_HOME) ก่อนเสมอ
    mc.send_angles(armconfig.POSE_HOME, speed)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    time.sleep(0.3)

    # 2. ท่าเต้นชูมือฉลองขึ้นฟ้า (เอนถอยหลัง J2<=0, ข้อศอกยกสูง J3<=0, เงยข้อมือขึ้นฟ้า J4=+60° ถึง +75°)
    # มั่นใจ 100% ไม่มีการก้มตัวลงหาพื้นโต๊ะหรือหอคอยกล่อง
    mc.send_angles([35, -5, -15, 60, 20, 45], speed); time.sleep(0.8)
    mc.send_angles([-35, -5, -15, 60, -20, -45], speed); time.sleep(0.8)
    mc.send_angles([30, 0, -20, 75, 0, 90], speed); time.sleep(0.8)
    mc.send_angles([-30, 0, -20, 75, 0, -90], speed); time.sleep(0.8)
    mc.send_angles(armconfig.POSE_HOME, speed); time.sleep(1.0)
    print(f"✅ <SYSTEM>: DONE TASK - Dance (Victory)")
    return {"status": "DONE TASK"}


# ── gesture ──────────────────────────────────────────────────────────────────

def raw_gesture(action: str) -> str:
    action = action.lower()
    valid_actions = ("yes", "no", "bow", "wave", "confused")
    if action not in valid_actions:
        return f"Error: action must be one of {valid_actions}."

    err = _put_down_held("กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อนทำท่าทาง...")
    if err:
        return err

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
        mc.send_angles([base[0], base[1], base[2], 65, base[4], j6 + 45], speed); time.sleep(0.6)
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
        # Pass target_height=None so raw_move_to calculates proper layer stacking height automatically
        res_move = raw_move_to(target_coord=corner_coord)
        if isinstance(res_move, dict) and res_move.get("status") == "ERROR":
            return res_move

    print(f"✅ <SYSTEM>: DONE TASK - Clean desk ({len(found_objects)} objects)")
    return {"status": "DONE TASK", "message": f"จัดเก็บ {len(found_objects)} ชิ้นเข้ามุมแล้ว"}

# ── play_rps ─────────────────────────────────────────────────────────────────

def raw_play_rps_game() -> dict:
    err = _put_down_held("กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อนเล่นเกม...")
    if err:
        return err

    from agent.tools.shares.rps_game import raw_play_rps_game as _play
    return _play()


# ── unstack_and_grab ─────────────────────────────────────────────────────────

def _select_buried_object(eng_name: str, is_generic_query: bool) -> str:
    """Pick (from memory) an object that has something stacked above it; keeps eng_name if none found."""
    for obj_a, coord_a in init.known_objects.items():
        if _is_placed(obj_a, coord_a):
            za = _coord_z(coord_a)
            for obj_b, coord_b in init.known_objects.items():
                if obj_a != obj_b and _is_placed(obj_b, coord_b):
                    if _is_near_xy(coord_a, coord_b[0], coord_b[1]) and _coord_z(coord_b) > za + 10:
                        eng_name = obj_a
                        print(f"🤖 <SYSTEM>: [Auto-Select Buried Object] พบ '{obj_a}' กำลังโดน '{obj_b}' ทับอยู่!")
                        break
            if eng_name and is_generic_query:
                break
    return eng_name


def _blockers_above(eng_name: str, tx: float, ty: float, tz: float) -> list:
    """[(name, z)] of remembered objects stacked above the target at (tx, ty, tz)."""
    blockers = []
    for k, v in init.known_objects.items():
        if k == eng_name or not _is_placed(k, v):
            continue
        vz = _coord_z(v)
        if _is_near_xy(v, tx, ty) and vz > tz + 10:
            blockers.append((k, vz))
    return blockers


def _rescan_blockers(eng_name: str, tx: float, ty: float, tz: float) -> list:
    """Scan the desk once, then look for blockers again (empty list if the scan fails)."""
    try:
        from vision.yolo_detector import scan_with_yolo
        scan_with_yolo("cube")
        return _blockers_above(eng_name, tx, ty, tz)
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Unstack scan fallback error: {e}")
        return []


def _clear_blockers(blocking_objects: list):
    """Move each blocker (highest first) to a safe spot. Returns the failing result dict or None."""
    for b_name, b_z in blocking_objects:
        print(f"🤖 <SYSTEM>: [Unstack Step] กำลังหยิบ '{b_name}' ออกไปวางที่พื้นที่ปลอดภัย...")
        res_grab = raw_grab_object(b_name, _auto_unstack=False)
        if isinstance(res_grab, dict) and res_grab.get("status") == "ERROR":
            print(f"⚠️ <SYSTEM>: ล้มเหลวขณะพยายามหยิบ '{b_name}' ออก")
            return res_grab

        # ย้ายไปวางในตำแหน่งที่ปลอดภัย
        safe_coord = raw_find_safe_spot()
        res_move = raw_move_to(target_coord=safe_coord)
        if isinstance(res_move, dict) and res_move.get("status") == "ERROR":
            print(f"⚠️ <SYSTEM>: ล้มเหลวขณะพยายามวาง '{b_name}' ลงพื้นที่ปลอดภัย")
            return res_move
    return None


def raw_unstack_and_grab(object_name: str, safe_area: str = "blank_area") -> dict:
    """Check if object is blocked by stacked items, unstack them to safe_area, then grab the target object."""
    err = _put_down_held("[Unstack] กริปเปอร์ถือ '{held}' อยู่ → วางลงตำแหน่งที่ปลอดภัยอัตโนมัติก่อน...")
    if err:
        return err

    eng_name = get_english_name(object_name)
    
    # 1. If generic target like "กล่องที่โดนทับ" or "buried_cube", find which object in memory is blocked
    is_generic_query = any(w in object_name.lower() for w in ["โดนทับ", "ทับอยู่", "ข้างล่าง", "ชั้นล่าง", "buried", "bottom"])

    if is_generic_query or not eng_name or eng_name not in init.known_objects:
        eng_name = _select_buried_object(eng_name, is_generic_query)

    # 2. MEMORY FIRST: Find target coordinates with strict color matching
    found_key, target_coord = _find_in_memory(eng_name)
    if found_key and target_coord:
        eng_name = found_key

    # 3. SCAN IF NOT IN MEMORY
    if not target_coord:
        target_coord = _scan_unstack_target(eng_name, object_name)
        if not target_coord:
            return raw_grab_object(object_name)
            
    tx, ty = float(target_coord[0]), float(target_coord[1])
    tz = float(target_coord[2]) if len(target_coord) >= 3 and target_coord[2] > 0 else armconfig.GRAB_BASE_HEIGHT
    
    # 4. Find all blocking objects stacked on top of target_coord
    blocking_objects = _blockers_above(eng_name, tx, ty, tz)

    # Fallback: If no blocking objects found in memory but user requested unstacking, scan desk once
    if not blocking_objects and is_generic_query:
        blocking_objects = _rescan_blockers(eng_name, tx, ty, tz)

    blocking_objects.sort(key=lambda x: x[1], reverse=True)

    # 5. Execute unstacking sequence
    if blocking_objects:
        print(f"🤖 <SYSTEM>: ตรวจพบวัตถุทับอยู่บน '{eng_name}' จำนวน {len(blocking_objects)} ชิ้น! เริ่มกระบวนการย้ายกล่องชั้นบนออก...")
        err = _clear_blockers(blocking_objects)
        if err:
            return err
    else:
        print(f"🤖 <SYSTEM>: ไม่มีวัตถุทับอยู่บน '{eng_name}' สามารถหยิบได้ทันที")

    print(f"🤖 <SYSTEM>: พื้นที่เปิดทางแล้ว! กำลังหยิบเป้าหมายหลัก '{eng_name}'...")
    return raw_grab_object(eng_name, target_coord=target_coord, _auto_unstack=False)


# ── scan_object ──────────────────────────────────────────────────────────────

def raw_scan_object(object_name: str) -> str:
    eng_name = get_english_name(object_name)
    from vision import yolo_detector

    # หากเป็นการสั่งสแกนภาพรวม / ตรวจสอบความจำทั้งหมดบนโต๊ะ
    if not eng_name or eng_name in ["cube", "block", "all", "all_objects", "box", ""]:
        verified = yolo_detector.verify_and_calibrate_memory()
        return {"status": "DONE TASK", "message": f"Memory verified 100%. Current known objects: {verified}"}

    # Memory First: check known_objects with strict color matching
    found_key, coord = _find_in_memory(eng_name)
    if found_key and coord:
        print(f"✅ <SYSTEM>: [Memory-First] พบ '{object_name}' ({found_key}) ในความจำแล้ว ที่ {coord}")
        return {"status": "DONE TASK", "message": f"Found '{object_name}' in memory at {coord}."}
        
    yolo_coord = yolo_detector.scan_with_yolo(eng_name or object_name)
    if yolo_coord:
        init.known_objects[eng_name] = yolo_coord
        print(f"✅ <SYSTEM>: DONE TASK - Scan {object_name}")
        return {"status": "DONE TASK", "message": f"Found '{object_name}' at {yolo_coord}. Memory updated."}
    return {"status": "ERROR", "message": f"'{object_name}' not found."}


# ── describe_scene ───────────────────────────────────────────────────────────

def raw_describe_scene(question: str = "มีอะไรอยู่บนโต๊ะบ้าง") -> dict:
    """Bend down to POSE_READY to view the table clearly, take photo, and ask vision model."""
    question = (str(question) if question is not None else "").strip() or "มีอะไรอยู่บนโต๊ะบ้าง"
    print(f"🤖 <SYSTEM>: [Describe Scene] ก้มกล้องมองโต๊ะเพื่อตอบคำถาม: '{question}'...")
    mc.send_angles(armconfig.POSE_READY, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_READY, mode="angles")
    time.sleep(1.0)
    
    # 1. Take a picture
    init.GetImage()
    image_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
    
    # 2. Return arm to home
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    
    # 3. Call the Vision API
    print("🤖 <SYSTEM>: กำลังวิเคราะห์ภาพ...")
    try:
        from vision import api
        result_text = api.QwenVLDescribe(question, image_path)
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Vision API error: {e}")
        result_text = f"เกิดข้อผิดพลาดในการวิเคราะห์ภาพ: {e}"
    finally:
        mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")

    print(f"✅ <SYSTEM>: DONE TASK - Describe scene:\n{result_text}")
    return {"status": "DONE TASK", "message": result_text, "result": result_text}



# ── move_around ──────────────────────────────────────────────────────────────

def raw_move_around(speed: int = 40) -> dict:
    """Performs a scanning animation to look around the environment."""
    print(f"🤖 <SYSTEM>: กำลังส่ายกล้องสำรวจรอบๆ ที่ความเร็ว {speed}...")
    mc.send_angles(armconfig.POSE_HOME, speed)
    time.sleep(2)
    mc.send_angles([60, 0, 0, 0, 0, -45], speed)
    time.sleep(2.5)
    mc.send_angles([-60, 0, 0, 0, 0, -45], speed)
    time.sleep(3.5)
    mc.send_angles([0, -30, -30, 0, 0, -45], speed)
    time.sleep(2.5)
    mc.send_angles(armconfig.POSE_HOME, speed)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    print("✅ <SYSTEM>: DONE TASK - Move around")
    return {"status": "DONE TASK"}


# ── give_to_person ───────────────────────────────────────────────────────────

def raw_give_to_person() -> dict:
    """Hands over currently held object to person in front of robot."""
    if not init.is_holding_object and not init.current_held_object:
        return {"status": "ERROR", "message": "หุ่นยนต์ไม่ได้ถืออะไรอยู่เลย"}
        
    held = init.current_held_object  # open_gripper() ล้างค่านี้ — เก็บไว้ก่อน
    print("🤖 <SYSTEM>: กำลังยื่นของไปให้ที่ด้านหน้า...")
    target_coord = [180.0, 0.0, 150.0]
    
    current_coords = mc.safe_get_coords()
    if current_coords and len(current_coords) >= 3:
        lift_target = [current_coords[0], current_coords[1], armconfig.Z_SAFE_TRAVEL]
        mc.send_coords(lift_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
        mc.wait_for_arrival(lift_target, mode="coords")
        
    xy_target = [target_coord[0], target_coord[1], armconfig.Z_SAFE_TRAVEL]
    mc.send_coords(xy_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(xy_target, mode="coords")
    
    final_target = [target_coord[0], target_coord[1], target_coord[2]]
    mc.send_coords(final_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(final_target, mode="coords")
    
    print("🤖 <SYSTEM>: มารับของไปได้เลยครับ จะปล่อยใน 4 วินาที...")
    time.sleep(4)
    init.open_gripper()
    time.sleep(1)
    
    mc.send_coords(xy_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(xy_target, mode="coords")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    
    if held:
        init.known_objects.pop(held, None)
    _drop_gripper_aliases()
    init.current_held_object = None
    init.is_holding_object = False
    
    print("✅ <SYSTEM>: DONE TASK - Handover to person")
    return {"status": "DONE TASK"}


# ── sort_by_color ────────────────────────────────────────────────────────────

def raw_sort_by_color() -> dict:
    """Automatically scans all colored blocks and sorts them into corner zones."""
    from vision.yolo_detector import scan_with_yolo
    from agent.tools.sort_by_color.color_zones import COLOR_ZONES, DEFAULT_ZONE
    
    print("🤖 <SYSTEM>: เริ่มต้นโหมดแยกสี (Sort by Color)...")
    found_objects = scan_with_yolo("cube")
    if not found_objects:
        return {"status": "DONE TASK", "message": "ไม่พบสิ่งของบนโต๊ะเลย"}
        
    # scan_with_yolo("cube") คืน known_objects ทั้งก้อน — เอาเฉพาะกล่องที่วางอยู่จริง (ไม่เอา area / in gripper)
    found_objects = {k: v for k, v in found_objects.items() if _is_placed(k, v) and "cube" in k.lower()}
    success_count = 0
    for full_name, coord in found_objects.items():
        target_zone = DEFAULT_ZONE
        for color, zone in COLOR_ZONES.items():
            if color in full_name:
                target_zone = zone
                break
                
        print(f"🤖 <SYSTEM>: กำลังแยกชิ้น '{full_name}' ไปที่โซนพิกัด {target_zone}...")
        init.known_objects[full_name] = coord
        grab_result = raw_grab_object(full_name)
        
        if isinstance(grab_result, dict) and grab_result.get("status") == "ERROR":
            print(f"⚠️ <SYSTEM>: หยิบ {full_name} ไม่สำเร็จ ข้ามไปชิ้นต่อไป...")
            continue
            
        if init.is_holding_object or init.current_held_object:
            res_move = raw_move_to(target_coord=target_zone)
            if isinstance(res_move, dict) and res_move.get("status") == "DONE TASK":
                success_count += 1
            
    mc.send_angles(armconfig.POSE_HOME, 40)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    print(f"✅ <SYSTEM>: DONE TASK - Sort by color ({success_count}/{len(found_objects)})")
    return {"status": "DONE TASK", "message": f"แยกสีสำเร็จ {success_count}/{len(found_objects)} ชิ้น"}


# ── execute_python_code ──────────────────────────────────────────────────────

def raw_execute_python_code(code: str) -> dict:
    """Executes python code and extracts Result variable."""
    try:
        exec_globals = {}
        exec(code, exec_globals)
        execution_result = exec_globals.get("Result", None)
        print(f"🤖 <SYSTEM>: Python Exec Result = {execution_result}")
        return {"status": "DONE TASK", "result": execution_result}
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Python Exec Error: {e}")
        return {"status": "ERROR", "message": str(e)}

