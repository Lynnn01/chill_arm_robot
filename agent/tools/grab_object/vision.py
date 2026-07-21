from hardware import init
from agent.tools.shares.vision_search import find_object_coord

def resolve_coord(object_name: str, target_coord: list = None) -> list | None:
    """หาพิกัดวัตถุจาก: explicit coord → memory → scan"""
    if target_coord and len(target_coord) >= 2:
        print(f"🤖 <SYSTEM>: กำลังขยับแขนกลไปหยิบของที่พิกัด {target_coord}...")
        return [float(target_coord[0]), float(target_coord[1])]
        
    if object_name in init.known_objects and isinstance(init.known_objects[object_name], list):
        saved_coord = init.known_objects[object_name]
        print(f"🤖 <SYSTEM>: ดึงพิกัด '{object_name}' จากความจำ {saved_coord} (ข้ามการสแกน)...")
        return [float(saved_coord[0]), float(saved_coord[1])]
        
    # Scan via YOLO / Qwen
    print(f"🤖 <SYSTEM>: กำลังใช้กล้องค้นหา '{object_name}'...")
    coord = find_object_coord(object_name)
    if coord:
        print(f"🤖 <SYSTEM>: เจอแล้ว! กำลังเคลื่อนที่ไปพิกัด {coord}")
    return coord
