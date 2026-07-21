import time
from hardware import init
from hardware.init import mc
from agents import function_tool
from .grab_object import grab_object
from .move_to import move_to
from vision.yolo_detector import scan_all_objects

@function_tool
def sort_by_color() -> str:
    """
    [Tags: Action, Sorting, Vision]
    Automatically scans the table for all colored blocks and sorts them into predefined corners by color.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "แยกสี", "จัดของตามสี", "เรียงสีให้หน่อย", "sort by color"
    - เครื่องมือนี้เป็นมาโคร (Macro) ที่จะทำงานแบบรวดเดียวจบ ห้ามเรียกใช้ซ้อนกับเครื่องมืออื่น
    """
    print("🤖 <SYSTEM>: เริ่มต้นโหมดแยกสี (Sort by Color)...")
    
    # 1. Panoramic Scan to find all objects
    found_objects = scan_all_objects()
    if not found_objects:
        return "ไม่พบสิ่งของบนโต๊ะเลยครับ ไม่สามารถแยกสีได้"
        
    # Default color zones (corners of the table)
    color_zones = {
        "red": [150.0, 150.0],     # Top-Right
        "blue": [-150.0, 150.0],   # Top-Left
        "green": [150.0, -150.0],  # Bottom-Right
        "yellow": [-150.0, -150.0] # Bottom-Left
    }
    
    success_count = 0
    # 2. Iterate through found objects and sort them
    for full_name, coord in found_objects.items():
        # Determine base color
        target_zone = [0, -150.0] # Default fallback
        for color, zone in color_zones.items():
            if color in full_name:
                target_zone = zone
                break
                
        print(f"🤖 <SYSTEM>: กำลังแยกชิ้น '{full_name}' ไปที่โซนพิกัด {target_zone}...")
        
        # We inject the known coordinate into grab_object to skip redundant scanning
        init.known_objects[full_name] = coord
        grab_result = grab_object(full_name)
        
        # Check if grab was successful
        if "Error:" not in grab_result and init.is_holding_object:
            move_to(target_zone)
            success_count += 1
        else:
            print(f"⚠️ <SYSTEM>: หยิบ {full_name} ไม่สำเร็จ ข้ามไปชิ้นต่อไป...")
            
    # Return to safe center
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    mc.wait_for_arrival([0, 0, 0, 0, 0, -45], mode="angles")
    
    return f"การแยกสีเสร็จสมบูรณ์ จัดการไปได้ทั้งหมด {success_count} ชิ้น จากที่พบ {len(found_objects)} ชิ้น"
