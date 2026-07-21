import time
from PIL import Image
from hardware.init import mc
from hardware import init
from agents import function_tool

@function_tool
def move_to(target_coord: list = None, target_name: str = None, target_height: int = 110) -> str:
    """
    [Tags: Action, Placement, Memory]
    Moves the currently grabbed object to a specific target coordinate [x, y] or on top of target_name and releases it.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "วาง", "ย้าย", "นำไปไว้ที่" พิกัดที่ระบุ หรือนำไปซ้อนกัน
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น ห้ามใช้ถ้ามือเปล่า
    
    Args:
        target_coord: The target coordinate [x, y] to place the object.
        target_name: The name of the object to place it on top of (e.g., 'green block').
        target_height: The height to release the object. Default is 110. For stacking, increase by 20.
    """
    if target_name and not target_coord:
        if target_name in init.known_objects and isinstance(init.known_objects[target_name], list):
            target_coord = init.known_objects[target_name]
        else:
            from vision import yolo_detector
            target_coord = yolo_detector.scan_with_yolo(target_name)
    
    if not target_coord:
        target_coord = init.last_coords[:2] if init.last_coords else [0, -150]

    # Auto-adjust height for stacking if target_height is default 110
    if target_height == 110:
        stack_count = 0
        for obj_name, coord in init.known_objects.items():
            if isinstance(coord, list) and len(coord) >= 2:
                # Check if coordinates are close (within 15 units)
                dx = abs(coord[0] - target_coord[0])
                dy = abs(coord[1] - target_coord[1])
                if dx < 15 and dy < 15:
                    stack_count += 1
        
        if stack_count > 0:
            # 32mm per block + 15mm drop gap to prevent pressing down
            target_height = 110 + (stack_count * 32) + 15
            print(f"🤖 <SYSTEM>: ตรวจพบวัตถุที่พิกัดนี้ {stack_count} ชิ้น ปรับความสูงการวางเป็น {target_height} เพื่อไม่ให้กดทับรุนแรง")

    import math
    # Safety clamps
    target_coord[0] = max(-280.0, min(280.0, float(target_coord[0])))
    target_coord[1] = max(-280.0, min(280.0, float(target_coord[1])))
    target_height = max(0, min(280, int(target_height)))
    
    # Base radius safety (prevent hitting its own body if Z is low)
    if target_height < 100:
        radius = math.sqrt(target_coord[0]**2 + target_coord[1]**2)
        if radius < 80:
            print(f"⚠️ <SYSTEM>: เป้าหมายอยู่ใกล้ฐานเกินไปและ Z ต่ำ ปรับให้ปลอดภัยขึ้น...")
            if radius > 0:
                scale = 80 / radius
                target_coord[0] = target_coord[0] * scale
                target_coord[1] = target_coord[1] * scale
            else:
                target_coord[0], target_coord[1] = 80, 0

    # Move the object to the target position
    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่เป้าหมายพิกัด {target_coord} ความสูง {target_height}...")

    # Safe Movement Sequence
    current_coords = mc.safe_get_coords()
    if current_coords and len(current_coords) >= 3:
        # 1. Lift Up current pos
        lift_target = [current_coords[0], current_coords[1], 200]
        mc.send_coords(lift_target + [-175, 0, -45], 40)
        mc.wait_for_arrival(lift_target, mode="coords")

    # 2. Move Horizontally at safe height
    xy_target = [target_coord[0], target_coord[1], 200]
    mc.send_coords(xy_target + [-175, 0, -45], 40)
    mc.wait_for_arrival(xy_target, mode="coords")

    # 3. Descend to target height
    final_target = [target_coord[0], target_coord[1], target_height]
    mc.send_coords(final_target + [-175, 0, -45], 40)
    mc.wait_for_arrival(final_target, mode="coords")
    
    init.open_gripper()
    time.sleep(0.5)

    # 4. Lift straight up after releasing
    mc.send_coords(xy_target + [-175, 0, -45], 40)
    mc.wait_for_arrival(xy_target, mode="coords")
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    mc.wait_for_arrival([0, 0, 0, 0, 0, -45], mode="angles")

    # Update Memory
    if init.current_held_object:
        init.known_objects[init.current_held_object] = [round(target_coord[0], 2), round(target_coord[1], 2)]
        init.current_held_object = None

    print("🤖 <SYSTEM>: วางวัตถุสำเร็จ (อัปเดตความจำแล้ว)")
    actual_coords = mc.safe_get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Objects arranged successfully. Current arm position: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return "Objects arranged successfully."
