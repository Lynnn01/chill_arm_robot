import time
from hardware.init import mc
from agents import function_tool

@function_tool
def dance_celebrate() -> str:
    """
    [Tags: Entertainment, Action]
    Performs a fun dancing or celebrating sequence with the robotic arm.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "เต้น", "ดีใจ", "ฉลอง" หรือเมื่อผู้ใช้ชมเชยว่าเก่งมาก
    """
    print("Dancing and celebrating! 💃🕺")
    speed = 60
    
    # Dance sequence
    # Sway left
    mc.send_angles([-45, 0, -20, 0, 0, -45], speed)
    time.sleep(1)
    
    # Sway right
    mc.send_angles([45, 0, -20, 0, 0, -45], speed)
    time.sleep(1)
    
    # Sway left and pitch up
    mc.send_angles([-45, 0, 30, -30, 0, -45], speed)
    time.sleep(1)
    
    # Sway right and pitch up
    mc.send_angles([45, 0, 30, -30, 0, -45], speed)
    time.sleep(1)
    
    # Return to base home
    mc.send_angles([0, 0, 0, 0, 0, -45], speed)
    time.sleep(1.5)
    
    return "Dance completed successfully."
