import time
from PIL import Image
from hardware.init import mc
from hardware import init
from agents import function_tool

@function_tool
def move_to(target_coord: list, target_height: int = 110) -> str:
    """
    [Tags: Action, Placement, Memory]
    Moves the currently grabbed object to a specific target coordinate [x, y] and releases it at target_height.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "วาง", "ย้าย", "นำไปไว้ที่" พิกัดที่ระบุ หรือนำไปซ้อนกัน
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น ห้ามใช้ถ้ามือเปล่า
    
    Args:
        target_coord: The target coordinate [x, y] to place the object. For complex patterns, calculate this using Python code first.
        target_height: The height to release the object. Default is 110. For stacking, increase by 20 for each subsequent object.
    """
    # Safety clamps
    target_coord[0] = max(-280.0, min(280.0, float(target_coord[0])))
    target_coord[1] = max(-280.0, min(280.0, float(target_coord[1])))
    target_height = max(0, min(280, int(target_height)))

    width, height = Image.open("captured_image.jpg").size

    # Move the object to the target position
    print(f"🤖 <SYSTEM>: กำลังเคลื่อนย้ายวัตถุไปวางที่เป้าหมายพิกัด {target_coord} ความสูง {target_height}...")

    mc.send_coords([target_coord[0], target_coord[1], 180, -175, 0, -45], 40)
    time.sleep(2.5)

    mc.send_coords([target_coord[0], target_coord[1], target_height, -175, 0, -45], 40)
    time.sleep(2)
    init.open_gripper()
    time.sleep(1)

    mc.send_coords([target_coord[0], target_coord[1], 200, -175, 0, -45], 40)
    time.sleep(2)
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(1)

    # Update Memory
    if init.current_held_object:
        init.known_objects[init.current_held_object] = [round(target_coord[0], 2), round(target_coord[1], 2)]
        init.current_held_object = None

    print("🤖 <SYSTEM>: วางวัตถุสำเร็จ (อัปเดตความจำแล้ว)")
    actual_coords = mc.get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Objects arranged successfully. Current arm position: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return "Objects arranged successfully."
