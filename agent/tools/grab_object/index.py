from agents import function_tool
from .vision import resolve_coord
from .motion import execute_grab

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
    coord = resolve_coord(object_name, target_coord)
    if not coord:
        return f"Error: มองไม่เห็น '{object_name}' บนโต๊ะเลยครับ ขอยกเลิกการหยิบ"
    return execute_grab(object_name, coord)
