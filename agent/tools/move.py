import time
from hardware.init import mc
from agents import function_tool
import armconfig

@function_tool
def move(x: float, y: float, z: float, speed: int = 40) -> str:
    """
    [Tags: Action, Movement]
    Moves the robotic arm freely to the specified (x, y, z) coordinates without interacting with objects.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้หุ่นยนต์ขยับมือไปยังพิกัด X, Y, Z หรือทิศทางต่างๆ โดย "ไม่ได้ต้องการให้หยิบหรือวางอะไร" (เช่น เลื่อนมือไปทางซ้าย ขยับไปดูใกล้ๆ)
    
    Args:
        x: The target X coordinate (Forward). Safe range is -280 to 280.
        y: The target Y coordinate (Left/Right). Safe range is -280 to 280.
        z: The target Z coordinate (Height). Z=200 is hover, Z=110 is table level. Safe range is 0 to 280.
        speed: Movement speed (1-100). Default is 40.
    """
    import math
    
    # Safety clamps
    x = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(x)))
    y = max(armconfig.COORD_XY_MIN, min(armconfig.COORD_XY_MAX, float(y)))
    z = max(armconfig.COORD_Z_MIN, min(armconfig.COORD_Z_MAX, float(z)))
    
    # Base radius safety (prevent hitting its own body if Z is low)
    if z < 100:
        radius = math.sqrt(x**2 + y**2)
        if radius < armconfig.GRAB_MIN_RADIUS:
            print(f"⚠️ <SYSTEM>: พิกัด (X:{x}, Y:{y}) อยู่ใกล้ฐานเกินไปและ Z ต่ำ ปรับให้ปลอดภัยขึ้น...")
            if radius > 0:
                scale = armconfig.GRAB_MIN_RADIUS / radius
                x = x * scale
                y = y * scale
            else:
                x, y = armconfig.GRAB_MIN_RADIUS, 0

    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่พิกัด (X:{x}, Y:{y}, Z:{z}) ด้วยความเร็ว {speed}...")
    
    current_coords = mc.safe_get_coords()
    if current_coords and len(current_coords) >= 3:
        # Safe Movement Sequence: 1. Lift Up, 2. Move X,Y, 3. Descend
        # 1. Lift
        lift_target = [current_coords[0], current_coords[1], armconfig.Z_SAFE_TRAVEL]
        mc.send_coords(lift_target + armconfig.WRIST_PLACE, speed)
        mc.wait_for_arrival(lift_target, mode="coords")
        
    # 2. Move Horizontally at safe height
    xy_target = [x, y, armconfig.Z_SAFE_TRAVEL]
    mc.send_coords(xy_target + armconfig.WRIST_PLACE, speed)
    mc.wait_for_arrival(xy_target, mode="coords")
    
    # 3. Descend to target Z
    final_target = [x, y, z]
    mc.send_coords(final_target + armconfig.WRIST_PLACE, speed)
    mc.wait_for_arrival(final_target, mode="coords")
    
    actual_coords = mc.safe_get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Moved successfully. Verified current coordinates are: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
