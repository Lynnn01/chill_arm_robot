import json
from PIL import Image
from vision import api
from hardware import init
from vision import eyeonhand
from agents import function_tool

@function_tool
def scan_object(object_name: str) -> str:
    """
    Uses the camera to scan the environment for a specific object.
    If found, the AI will remember its coordinates for future use.
    
    Args:
        object_name: The descriptive name of the object to search for (e.g., "red block").
    """
    print(f"🤖 <SYSTEM>: กำลังใช้กล้องสแกนหา '{object_name}'...")
    init.GetImage()
    
    try:
        width, height = Image.open('captured_image.jpg').size
        positions = api.QwenVLRequest("a " + object_name, "captured_image.jpg").get("coordinates", [])
    except Exception as e:
        print(f"🤖 <SYSTEM>: เกิดข้อผิดพลาดในการประมวลผลภาพ: {e}")
        return f"Error analyzing image: {e}"

    if positions:
        position = positions[0]
        # Calculate center point coordinates
        center_x = (position['x1'] + position['x2']) / 2
        center_y = (position['y1'] + position['y2']) / 2
        target_pixel = (center_x / 1000 * width, center_y / 1000 * height)
        
        robot_coord = eyeonhand.pixel_to_arm(target_pixel)
        
        with open("config.json", "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)
            
        x_offset = config_data.get("x", 0)
        y_offset = config_data.get("y", 0)
        
        robot_coord[0] = robot_coord[0] + x_offset
        robot_coord[1] = robot_coord[1] + y_offset
        
        if robot_coord[0] > 210:
            robot_coord[0] = robot_coord[0] - 5
            
        # Safety clamps
        robot_coord[0] = max(-280.0, min(280.0, float(robot_coord[0])))
        robot_coord[1] = max(-280.0, min(280.0, float(robot_coord[1])))
        
        # Save to memory
        saved_coord = [round(robot_coord[0], 2), round(robot_coord[1], 2)]
        init.known_objects[object_name] = saved_coord
        
        print(f"🤖 <SYSTEM>: สแกนพบ '{object_name}' ที่พิกัด {saved_coord} (บันทึกลงความจำแล้ว)")
        return f"Found '{object_name}' at {saved_coord}. Memory updated."
    else:
        print(f"🤖 <SYSTEM>: สแกนไม่พบ '{object_name}' ในบริเวณนี้")
        return f"Could not find '{object_name}'."
