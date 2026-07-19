import os
import time
import math
from hardware import init
from hardware.init import mc, cam_manager
from vision import eyeonhand

# Lazy load model
_model = None

def get_yolo_model():
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
            model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "cube_detect.pt")
            if os.path.exists(model_path):
                _model = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
        except ImportError:
            print("⚠️ <SYSTEM>: ไม่พบไลบรารี ultralytics (pip install ultralytics)")
    return _model

def scan_with_yolo(object_name):
    """
    Scans the environment using YOLO model first.
    Returns: robot_coord (list of [x, y]) if found, else None
    """
    model = get_yolo_model()
    if not model:
        return None
        
    print(f"🤖 <SYSTEM>: เริ่มการสแกนเร็วด้วย YOLO ค้นหา '{object_name}'...")
    scan_angles = [0, 45, 90, -45, -90]
    
    import json
    with open(init.CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    x_offset = config_data.get("x", 0)
    y_offset = config_data.get("y", 0)
    
    # รอ 5 วินาทีเพื่อให้ระบบ YOLO โหลดเสร็จและพร้อมทำงานก่อนเริ่มขยับ
    time.sleep(5.0)
    
    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: YOLO หันกล้องไปที่มุม {j1} องศา...")
        mc.send_angles([17.75 + j1, -0.79, 0.35, -75, 1.14, -28.12], 40)
        time.sleep(2.5)
        
        frame = cam_manager.get_frame()
        if frame is None:
            continue
            
        results = model(frame, verbose=False)
        annotated_frame = results[0].plot()
        cam_manager.set_overlay(annotated_frame, duration=2.0)
        
        # หน่วงเวลา 2 วินาทีเพื่อให้ผู้ใช้เห็นกรอบจับวัตถุบนหน้าจอก่อนขยับไปมุมอื่น
        time.sleep(2.0)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                name = model.names[cls]
                
                # Simple matching logic: if any word matches
                # e.g., "red" in "red_cube"
                obj_lower = object_name.lower().replace("_", " ")
                name_lower = name.lower().replace("_", " ")
                
                # Check for direct match or substring match (like "red" in "red cube")
                if any(word in name_lower for word in obj_lower.split()) or any(word in obj_lower for word in name_lower.split()):
                    # Found!
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    
                    target_pixel = (center_x, center_y)
                    robot_coord = eyeonhand.pixel_to_arm(target_pixel)
                    
                    robot_coord[0] = robot_coord[0] + x_offset
                    robot_coord[1] = robot_coord[1] + y_offset
                    
                    theta = math.radians(j1)
                    x_local = float(robot_coord[0])
                    y_local = float(robot_coord[1])
                    
                    x_world = x_local * math.cos(theta) - y_local * math.sin(theta)
                    y_world = x_local * math.sin(theta) + y_local * math.cos(theta)
                    
                    robot_coord[0] = x_world
                    robot_coord[1] = y_world
                    
                    if robot_coord[0] > 210:
                        robot_coord[0] = robot_coord[0] - 5
                        
                    robot_coord[0] = max(-280.0, min(280.0, float(robot_coord[0])))
                    robot_coord[1] = max(-280.0, min(280.0, float(robot_coord[1])))
                    
                    saved_coord = [round(robot_coord[0], 2), round(robot_coord[1], 2)]
                    
                    print(f"🤖 <SYSTEM>: YOLO เจอ '{name}' ที่มุม {j1}! พิกัดโลก: {saved_coord}")
                    # Return to center
                    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
                    time.sleep(1)
                    return saved_coord
                    
    print(f"🤖 <SYSTEM>: YOLO สแกนครบ 5 มุมแล้ว ไม่พบ '{object_name}' (จะสลับไปใช้ Vision AI API)")
    # Return to center for the next stage
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(1)
    return None
