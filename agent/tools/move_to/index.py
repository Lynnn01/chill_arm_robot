from agents import function_tool
from agent.tools.shares._raw import raw_move_to

@function_tool
def move_to(target_coord: list[float] = None, target_name: str = None, target_height: int = 110) -> str:
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
    result = raw_move_to(target_coord, target_name, target_height)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "Objects arranged successfully."
            
    return "Objects arranged successfully."
