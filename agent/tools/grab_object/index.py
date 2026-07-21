from agents import function_tool
from agent.tools.shares._raw import raw_grab_object

@function_tool
def grab_object(object_name: str, target_coord: list[float] = None) -> str:
    """
    [Tags: Action, Vision, Memory]
    Uses computer vision to detect and grab the specified object from the workspace.
    If target_coord is provided, it skips vision and grabs directly from that location.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "หยิบ", "จับ", "เอา" วัตถุที่ระบุ
    - ระบบจะตรวจสอบ Memory อัตโนมัติ หากเจอพิกัดจะหยิบเลย หากไม่เจอจะใช้กล้องสแกนก่อน
    
    Args:
        object_name: The descriptive name of the object to grab (e.g., "red block", "blue cube").
        target_coord: Optional [x, y] coordinates to grab from. If provided, vision is skipped.
    """
    result = raw_grab_object(object_name, target_coord)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            coord = result.get("data")
            return f"Successfully grabbed {object_name} at coordinates {coord}"
    
    return f"Successfully grabbed {object_name}"
