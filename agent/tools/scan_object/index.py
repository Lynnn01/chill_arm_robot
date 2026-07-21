from agents import function_tool
from .yolo_scan import scan_with_yolo
from .ai_scan import scan_with_ai
from hardware import init

@function_tool
def scan_object(object_name: str) -> str:
    """
    [Tags: Vision, Memory, Search]
    Uses the camera to scan the environment for a specific object.
    If found, the AI will remember its coordinates for future use.
    
    When to use: 
    - เมื่อผู้ใช้ถามหาตำแหน่งของสิ่งของ หรือสั่งให้มองหา/สแกนหาสิ่งของ
    - ห้ามใช้ถ้าผู้ใช้สั่งให้ "หยิบ" (ใช้ grab_object แทน)
    
    Args:
        object_name: The descriptive name of the object to search for (e.g., "red block").
    """
    # 1. Fast Scan with YOLO
    yolo_coord = scan_with_yolo(object_name)
    if yolo_coord:
        init.known_objects[object_name] = yolo_coord
        return f"Found '{object_name}' at {yolo_coord}. Memory updated."

    # 2. Fallback to Vision AI (Qwen)
    print(f"🤖 <SYSTEM>: กำลังใช้กล้องสแกนหา '{object_name}' ด้วย Vision AI (ทั้งหมด 5 มุม)...")
    coord = scan_with_ai(object_name)
    if coord:
        init.known_objects[object_name] = coord
        return f"Found '{object_name}' at {coord}. Memory updated."

    return f"Could not find '{object_name}'."
