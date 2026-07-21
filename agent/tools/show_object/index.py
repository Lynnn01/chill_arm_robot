from agents import function_tool
from agent.tools.shares._raw import raw_show_object

@function_tool
def show_object(object_name: str) -> str:
    """
    [Tags: Action, Interaction]
    Lifts the arm to present the currently grabbed object to the user or camera.
    
    When to use:
    - เมื่อถือของอยู่ แล้วผู้ใช้สั่งว่า "เอามาดูหน่อย", "โชว์ให้ดูหน่อย", "ยกขึ้นมา" เพื่อให้คนเห็นชัดๆ
    - ห้ามใช้ถ้าในมือยังไม่ได้ถืออะไรอยู่
    
    Args:
        object_name: The name of the object being shown.
    """
    result = raw_show_object(object_name)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "success"
            
    return "success"
