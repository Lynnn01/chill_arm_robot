import time
from tools import mc
from agents import function_tool

@function_tool
def move(x: float, y: float, z: float, speed: int = 40) -> str:
    """
    Moves the robotic arm freely to the specified (x, y, z) coordinates.
    The AI can use this to explore or position the arm dynamically.
    
    Args:
        x: The target X coordinate. Must be between -70 and 140.
        y: The target Y coordinate. Must be between 150 and 280.
        z: The target Z coordinate (height). Safe heights are usually above 100.
        speed: Movement speed (1-100). Default is 40.
    """
    print(f"Moving arm to (X:{x}, Y:{y}, Z:{z}) with speed {speed}...")
    
    # Send coordinates: [x, y, z, rx, ry, rz]. 
    # rx, ry, rz are kept at [-175, 0, -45] to keep the gripper facing downwards securely.
    mc.send_coords([x, y, z, -175, 0, -45], speed)
    time.sleep(3) # Wait for movement to complete
    
    return f"Moved successfully to X:{x}, Y:{y}, Z:{z}."
