from agents import function_tool
from agent.tools.shares._raw import raw_move_to

@function_tool
def move_to(target_coord: list[float] = None, target_name: str = None, target_height: int = 110, smart_place: bool = False) -> str:
    """
    [Tags: Action, Placement, Memory]
    Moves the currently grabbed object to a specific target coordinate [x, y], on top of target_name, or smart places it in a safe spot/stack and releases it.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "วาง", "ย้าย", "นำไปไว้ที่" พิกัดที่ระบุ, นำไปซ้อนกล่องอื่น หรือสุ่มวางในตำแหน่งที่ปลอดภัย
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น ห้ามใช้ถ้ามือเปล่า
    
    Args:
        target_coord: The target coordinate [x, y] to place the object (optional).
        target_name: The name of the object to place it on top of (e.g., 'green_cube') or 'random' / 'stack' (optional).
        target_height: The height to release the object. Default is 110. For stacking, auto-calculated if omitted.
        smart_place: If True, automatically stacks on known objects or picks a safe empty spot.
    """
    result = raw_move_to(target_coord, target_name, target_height, smart_place=smart_place)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "Objects arranged successfully."
            
    return "Objects arranged successfully."
