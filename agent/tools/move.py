import time
from hardware.init import mc
from agents import function_tool

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
    x = max(-280.0, min(280.0, float(x)))
    y = max(-280.0, min(280.0, float(y)))
    z = max(0.0, min(280.0, float(z)))
    
    # Base radius safety (prevent hitting its own body if Z is low)
    if z < 100:
        radius = math.sqrt(x**2 + y**2)
        if radius < 80:
            print(f"⚠️ <SYSTEM>: พิกัด (X:{x}, Y:{y}) อยู่ใกล้ฐานเกินไปและ Z ต่ำ ปรับให้ปลอดภัยขึ้น...")
            if radius > 0:
                scale = 80 / radius
                x = x * scale
                y = y * scale
            else:
                x, y = 80, 0

    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่พิกัด (X:{x}, Y:{y}, Z:{z}) ด้วยความเร็ว {speed}...")
    
    current_coords = mc.get_coords()
    if current_coords and len(current_coords) >= 3:
        # Safe Movement Sequence: 1. Lift Up, 2. Move X,Y, 3. Descend
        # 1. Lift
        mc.send_coords([current_coords[0], current_coords[1], 200, -175, 0, -45], speed)
        time.sleep(1.5)
        
    # 2. Move Horizontally at safe height
    mc.send_coords([x, y, 200, -175, 0, -45], speed)
    time.sleep(2.5)
    
    # 3. Descend to target Z
    mc.send_coords([x, y, z, -175, 0, -45], speed)
    time.sleep(1.5)
    
    actual_coords = mc.get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Moved successfully. Verified current coordinates are: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
