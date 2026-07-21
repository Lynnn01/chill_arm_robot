from agents import function_tool
from agent.tools.shares._raw import raw_move

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
    result = raw_move(x, y, z, speed)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
            
    return f"Moved successfully to target X:{x}, Y:{y}, Z:{z}."
