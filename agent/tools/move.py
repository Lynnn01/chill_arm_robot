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
    # Safety clamps
    x = max(-280.0, min(280.0, float(x)))
    y = max(-280.0, min(280.0, float(y)))
    z = max(0.0, min(280.0, float(z)))

    print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปที่พิกัด (X:{x}, Y:{y}, Z:{z}) ด้วยความเร็ว {speed}...")
    
    # Send coordinates: [x, y, z, rx, ry, rz]. 
    # rx, ry, rz are kept at [-175, 0, -45] to keep the gripper facing downwards securely.
    mc.send_coords([x, y, z, -175, 0, -45], speed)
    time.sleep(3) # Wait for movement to complete
    
    actual_coords = mc.get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Moved successfully. Verified current coordinates are: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
