import time
from hardware.init import mc
from agents import function_tool
import armconfig

@function_tool
def move_around(speed: int = 40) -> str:
    """
    [Tags: Action, Exploration]
    Performs a scanning animation to look around the environment.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "ส่ายกล้อง", "สำรวจรอบๆ", "มองไปรอบๆ" 
    - ระบบจะขยับหัวแบบสุ่ม/สแกนเพื่อมองหาอะไรใหม่ๆ โดยอัตโนมัติ
    
    Args:
        speed: The speed of the movement, ranging from 10 to 100. Default is 40.
    """
    print(f"Executing move around sequence at speed {speed}...")
    
    # 1. Move to default/center position
    mc.send_angles(armconfig.POSE_HOME, speed)
    time.sleep(3)
    
    # 2. Pan Left
    mc.send_angles([60, 0, 0, 0, 0, -45], speed)
    time.sleep(3)
    
    # 3. Pan Right (Sweep across)
    mc.send_angles([-60, 0, 0, 0, 0, -45], speed)
    time.sleep(4)
    
    # 4. Look Up slightly (adjusting joint 2 and 3)
    mc.send_angles([0, -30, -30, 0, 0, -45], speed)
    time.sleep(3)
    
    # 5. Return to default/center position
    mc.send_angles(armconfig.POSE_HOME, speed)
    time.sleep(3)
    
    print("Move around sequence completed.")
    return "Arm successfully moved around the environment."
