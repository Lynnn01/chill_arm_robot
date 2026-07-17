import json
import time
import math
from PIL import Image
from vision import api
from hardware import init
from vision import eyeonhand
from hardware.init import mc
from agents import function_tool

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
    print(f"🤖 <SYSTEM>: กำลังใช้กล้องสแกนหา '{object_name}' (ทั้งหมด 5 มุม)...")
    
    # 5-step scan angles for J1: Down-center, Left 45, Left 90, Right 45, Right 90
    scan_angles = [0, 45, 90, -45, -90]
    
    with open("config.json", "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
        
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)
    
    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: กำลังหันกล้องไปที่มุม {j1} องศา...")
        mc.send_angles([j1, 20, -30, -30, 0, -45], 40)
        time.sleep(2.5) # Wait for arm to stop and camera to stabilize
        
        init.GetImage()
        
        try:
            width, height = Image.open('captured_image.jpg').size
            positions = api.QwenVLRequest("a " + object_name, "captured_image.jpg").get("coordinates", [])
        except Exception as e:
            print(f"🤖 <SYSTEM>: เกิดข้อผิดพลาดในการประมวลผลภาพ: {e}")
            continue

        if positions:
            position = positions[0]
            # Calculate center point coordinates
            center_x = (position['x1'] + position['x2']) / 2
            center_y = (position['y1'] + position['y2']) / 2
            target_pixel = (center_x / 1000 * width, center_y / 1000 * height)
            
            # Map to arm coordinates (relative to current camera rotation)
            robot_coord = eyeonhand.pixel_to_arm(target_pixel)
            
            # Add general offsets
            robot_coord[0] = robot_coord[0] + x_offset
            robot_coord[1] = robot_coord[1] + y_offset
            
            # Apply Rotation Matrix to convert to absolute world coordinates
            # J1 positive means turning LEFT (counter-clockwise).
            # Math: 
            # x' = x*cos(theta) - y*sin(theta)
            # y' = x*sin(theta) + y*cos(theta)
            theta = math.radians(j1)
            x_local = float(robot_coord[0])
            y_local = float(robot_coord[1])
            
            x_world = x_local * math.cos(theta) - y_local * math.sin(theta)
            y_world = x_local * math.sin(theta) + y_local * math.cos(theta)
            
            robot_coord[0] = x_world
            robot_coord[1] = y_world
            
            if robot_coord[0] > 210:
                robot_coord[0] = robot_coord[0] - 5
                
            # Safety clamps
            robot_coord[0] = max(-280.0, min(280.0, float(robot_coord[0])))
            robot_coord[1] = max(-280.0, min(280.0, float(robot_coord[1])))
            
            # Save to memory
            saved_coord = [round(robot_coord[0], 2), round(robot_coord[1], 2)]
            init.known_objects[object_name] = saved_coord
            
            print(f"🤖 <SYSTEM>: เจอแล้ว! สแกนพบ '{object_name}' ที่มุม {j1} องศา (พิกัดโลก: {saved_coord})")
            
            # กลับมาท่าตั้งต้น
            mc.send_angles([0, 0, 0, 0, 0, -45], 40)
            return f"Found '{object_name}' at {saved_coord}. Memory updated."
            
        else:
            print(f"🤖 <SYSTEM>: สแกนมุม {j1} องศา ไม่พบ '{object_name}'")

    print(f"🤖 <SYSTEM>: สแกนครบ 5 มุมแล้ว ไม่พบ '{object_name}' ในบริเวณนี้")
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    return f"Could not find '{object_name}'."
