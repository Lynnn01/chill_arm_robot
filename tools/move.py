import time
from tools import mc
from agents import function_tool

@function_tool
def move(x: float, y: float, z: float, speed: int = 40) -> str:
    """
    Moves the robotic arm freely to the specified (x, y, z) coordinates.
    The AI can use this to explore or position the arm dynamically.
    
    Args:
        x: The target X coordinate (Forward). Safe range is 140 to 280.
        y: The target Y coordinate (Left/Right). Safe range is -100 to 100.
        z: The target Z coordinate (Height). Z=200 is hover, Z=110 is table level. Safe range is 100 to 250.
        speed: Movement speed (1-100). Default is 40.
    """
    # Safety clamps
    x = max(140.0, min(280.0, float(x)))
    y = max(-100.0, min(100.0, float(y)))
    z = max(100.0, min(250.0, float(z)))

    print(f"Moving arm to (X:{x}, Y:{y}, Z:{z}) with speed {speed}...")
    
    # Send coordinates: [x, y, z, rx, ry, rz]. 
    # rx, ry, rz are kept at [-175, 0, -45] to keep the gripper facing downwards securely.
    mc.send_coords([x, y, z, -175, 0, -45], speed)
    time.sleep(3) # Wait for movement to complete
    
    actual_coords = mc.get_coords()
    if actual_coords and len(actual_coords) >= 3:
        return f"Moved successfully. Verified current coordinates are: X:{actual_coords[0]}, Y:{actual_coords[1]}, Z:{actual_coords[2]}."
    return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
