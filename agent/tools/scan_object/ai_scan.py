import time
import os
import math
from PIL import Image
import armconfig
from hardware.init import mc
from hardware import init
from vision import api
from agent.tools.shares.vision_search import apply_rotation, clamp_xy
from agent.tools.shares.coord_transform import pixel_center
from vision import eyeonhand
from agent.tools.shares.config_loader import load_offsets

def scan_with_ai(object_name: str) -> list | None:
    """Scan using Qwen across multiple angles"""
    scan_angles = armconfig.SCAN_ANGLES
    cfg = load_offsets()
    
    for j1 in scan_angles:
        print(f"🤖 <SYSTEM>: กำลังหันกล้องไปที่มุม {j1} องศา...")
        current_ready = armconfig.POSE_READY.copy()
        current_ready[0] = current_ready[0] + j1
        mc.send_angles(current_ready, armconfig.SPEED_GRAB)
        time.sleep(armconfig.SCAN_WAIT_PER_ANGLE)
        
        init.GetImage()
        print(f"🤖 <SYSTEM>: ถ่ายภาพมุม {j1} องศาสำเร็จ กำลังส่งให้ Vision AI วิเคราะห์... (รอคำตอบ)")
        
        try:
            img_path = os.path.join(init.PROJECT_ROOT, "captured_image.jpg")
            width, height = Image.open(img_path).size
            positions = api.QwenVLRequest("a " + object_name, img_path).get("coordinates", [])
        except Exception as e:
            print(f"🤖 <SYSTEM>: เกิดข้อผิดพลาดในการประมวลผลภาพ: {e}")
            continue

        if positions:
            pos = positions[0]
            cx, cy = pixel_center(pos)
            target_pixel = (cx / 1000 * width, cy / 1000 * height)
            
            coord_np = eyeonhand.pixel_to_arm(target_pixel)
            coord = [float(coord_np[0]) + cfg["x"], float(coord_np[1]) + cfg["y"]]
            
            if j1 != 0:
                coord = apply_rotation(coord, j1)
                
            if coord[0] > 210:
                coord[0] = coord[0] - 5
                
            coord = clamp_xy(coord)
            saved_coord = [round(coord[0], 2), round(coord[1], 2)]
            
            print(f"🤖 <SYSTEM>: เจอแล้ว! สแกนพบ '{object_name}' ที่มุม {j1} องศา (พิกัดโลก: {saved_coord})")
            
            mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
            return saved_coord
        else:
            print(f"🤖 <SYSTEM>: สแกนมุม {j1} องศา ไม่พบ '{object_name}'")

    print(f"🤖 <SYSTEM>: สแกนครบ {len(scan_angles)} มุมแล้ว ไม่พบ '{object_name}' ในบริเวณนี้")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    return None
