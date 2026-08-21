from agents import function_tool
from agent.tools.shares._raw import raw_smart_place

@function_tool
def smart_place(prefer_stack: bool = True) -> str:
    """
    [Tags: Action, Placement, Autonomous]
    Autonomously places the currently held object by either stacking it onto another known object or finding a random safe spot on the desk.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "วางซ้อน", "วางไว้ที่ไหนก็ได้", "สุ่มวาง", "หาที่วางที่ปลอดภัย"
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น
    
    Args:
        prefer_stack: If True (default), tries to stack onto other objects first. If False, places in a safe empty spot.
    """
    result = raw_smart_place(prefer_stack=prefer_stack)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "Object placed successfully."
            
    return "Object placed successfully."
