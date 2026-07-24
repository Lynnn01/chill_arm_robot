import time
import armconfig
from hardware import init

def calculate_and_move(cx: float, cy: float, center_x: float, center_y: float, target_angles: list, last_send_time: float) -> tuple:
    """
    คำนวณ PID Tracking และสั่งแขนกลขยับ
    Returns: (target_angles_ใหม่, last_send_time_ใหม่)
    """
    pan_error = center_x - cx
    tilt_error = center_y - cy
    
    # ถ้ามีการกลับซ้าย-ขวาที่กล้อง ต้องสลับทิศทางการหัน (Pan) ของหุ่นด้วย
    if getattr(armconfig, 'CAMERA_FLIP_HORIZONTAL', False):
        pan_error = -pan_error
    
    if abs(pan_error) > armconfig.TRACKING_DEADZONE_PX or abs(tilt_error) > armconfig.TRACKING_DEADZONE_PX:
        Kp = armconfig.TRACKING_KP
        
        new_j1 = target_angles[0] + (pan_error * Kp)
        new_j4 = target_angles[3] + (tilt_error * Kp)
        
        new_j1 = max(armconfig.TRACKING_J1_MIN, min(armconfig.TRACKING_J1_MAX, new_j1))
        new_j4 = max(armconfig.TRACKING_J4_MIN, min(armconfig.TRACKING_J4_MAX, new_j4))
        
        if abs(new_j1 - target_angles[0]) > 0.5 or abs(new_j4 - target_angles[3]) > 0.5:
            target_angles[0] = new_j1
            target_angles[3] = new_j4
            
            if time.time() - last_send_time > armconfig.TRACKING_SEND_INTERVAL:
                init.mc.send_angles(target_angles, armconfig.SPEED_TRACKING)
                last_send_time = time.time()
                
    return target_angles, last_send_time
