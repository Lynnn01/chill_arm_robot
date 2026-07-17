import time
from hardware.init import mc
from agents import function_tool

@function_tool
def gesture(action: str) -> str:
    """
    [Tags: Entertainment, Action]
    Performs a gesture to communicate non-verbally.
    
    When to use:
    - เมื่อผู้ใช้ถามคำถามที่ตอบใช่/ไม่ใช่ แล้วเราต้องการแสดงท่าทางแทนคำพูด ("พยักหน้า", "ส่ายหน้า") หรือทักทาย ("โบกมือ")
    
    Args:
        action: Must be either "yes" (nodding) or "no" (shaking head).
    """
    action = action.lower()
    if action not in ["yes", "no"]:
        return "Error: Action must be 'yes' or 'no'."
        
    print(f"Performing gesture: {action.upper()}")
    speed = 60
    
    # Try to get current angles to return to them later
    current_angles = mc.get_angles()
    if not current_angles or len(current_angles) != 6:
        base_angles = [0, 0, 0, 0, 0, -45]
    else:
        base_angles = current_angles

    if action == "yes":
        # Nodding: Move joint 5 (wrist pitch) up and down
        j5_base = base_angles[4]
        # Up
        mc.send_angle(5, j5_base + 30, speed)
        time.sleep(0.5)
        # Down
        mc.send_angle(5, j5_base - 30, speed)
        time.sleep(0.6)
        # Up
        mc.send_angle(5, j5_base + 30, speed)
        time.sleep(0.6)
        # Return
        mc.send_angle(5, j5_base, speed)
        time.sleep(0.5)
        return "Nodded YES."
        
    elif action == "no":
        # Shaking head: Move joint 1 (base) left and right
        j1_base = base_angles[0]
        # Left
        mc.send_angle(1, j1_base + 30, speed)
        time.sleep(0.5)
        # Right
        mc.send_angle(1, j1_base - 30, speed)
        time.sleep(0.6)
        # Left
        mc.send_angle(1, j1_base + 30, speed)
        time.sleep(0.6)
        # Return
        mc.send_angle(1, j1_base, speed)
        time.sleep(0.5)
        return "Shook head NO."
