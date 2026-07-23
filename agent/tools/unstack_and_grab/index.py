from agents import function_tool
from agent.tools.shares._raw import raw_unstack_and_grab

@function_tool
def unstack_and_grab(object_name: str, safe_area: str = "blank_area") -> str:
    """
    [Tags: Action, Memory, Unstack]
    Uses computer vision and memory to safely grab an object that is buried under other objects.
    It will autonomously grab and move any blocking objects to a safe area before grabbing the target.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้หยิบของที่โดนทับอยู่ เช่น "หยิบของที่โดนทับ", "แกะกล่องที่ซ้อนกัน", "หยิบกล่องสีเขียวที่อยู่ข้างล่าง"
    - หรือเมื่อ AI วิเคราะห์สถานการณ์พบว่า object ที่ต้องการน่าจะโดนทับอยู่
    
    Args:
        object_name: The descriptive name of the object to grab (e.g., "green block").
        safe_area: (Optional) The area to place blocking objects. Default is "blank_area".
    """
    result = raw_unstack_and_grab(object_name, safe_area)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            coord = result.get("data")
            return f"Successfully unstacked (if needed) and grabbed {object_name} at coordinates {coord}"
    
    return f"Successfully unstacked and grabbed {object_name}"
