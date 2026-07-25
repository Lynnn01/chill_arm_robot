import time
from hardware.init import mc
from hardware import init
from agents import function_tool
import armconfig

@function_tool
def give_to_person() -> str:
    """
    [Tags: Action, Interaction]
    Hands over the currently held object to a person. It extends the arm forward and releases the object after 4 seconds.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "ส่งของให้ฉันหน่อย", "เอามาให้ฉัน", "ยื่นให้หน่อย"
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น ห้ามใช้ถ้ามือเปล่า
    - ห้ามใช้คำสั่งนี้เด็ดขาดถ้าผู้ใช้แค่สั่งให้ "วาง", "โชว์", หรือถ้าเป็นโหมด Auto แล้วไม่มีใครอยู่รับของ
    """
    if not init.is_holding_object:
        return "Error: หุ่นยนต์ไม่ได้ถืออะไรอยู่เลย กรุณาสั่งให้หยิบของก่อน"
        
    print("🤖 <SYSTEM>: กำลังยื่นของไปให้ที่ด้านหน้า...")
    
    # Target handover position (forward, safe height)
    target_coord = [180.0, 0.0, 150.0]
    
    # Safe Movement Sequence
    current_coords = mc.safe_get_coords()
    if current_coords and len(current_coords) >= 3:
        # 1. Lift Up current pos
        lift_target = [current_coords[0], current_coords[1], armconfig.Z_SAFE_TRAVEL]
        mc.send_coords(lift_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
        mc.wait_for_arrival(lift_target, mode="coords")
        
    # 2. Move Horizontally to handover X,Y
    xy_target = [target_coord[0], target_coord[1], armconfig.Z_SAFE_TRAVEL]
    mc.send_coords(xy_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(xy_target, mode="coords")
    
    # 3. Descend to handover height
    final_target = [target_coord[0], target_coord[1], target_coord[2]]
    mc.send_coords(final_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(final_target, mode="coords")
    
    print("🤖 <SYSTEM>: มารับของไปได้เลยครับ จะปล่อยใน 4 วินาที...")
    
    # Wait for person to grasp
    time.sleep(4)
    
    init.open_gripper()
    time.sleep(1)
    
    # 4. Lift straight up and return to center
    mc.send_coords(xy_target + armconfig.WRIST_PLACE, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(xy_target, mode="coords")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    mc.wait_for_arrival(armconfig.POSE_HOME, mode="angles")
    
    # Update Memory
    if init.current_held_object:
        init.known_objects.pop(init.current_held_object, None)
        init.current_held_object = None
        
    return "Successfully handed the object to the user."
