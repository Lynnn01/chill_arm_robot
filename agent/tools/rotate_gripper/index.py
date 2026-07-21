from agents import function_tool
from agent.tools.shares._raw import raw_rotate_gripper

@function_tool
def rotate_gripper(angle_range: int = 45, speed: int = 40) -> str:
    """
    [Tags: Action, Orientation]
    Rotates the gripper back and forth by a specified angle range, then returns to its original position.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "หมุนข้อมือ", "หมุนหัวจับ", "บิด" เพื่อเปลี่ยนมุมหรือโชว์ลูกเล่น
    
    Args:
        angle_range: The angle in degrees to rotate left and right. Default is 45.
        speed: Rotation speed (1-100). Default is 40.
    """
    result = raw_rotate_gripper(angle_range, speed)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "Gripper rotated successfully."
            
    return "Gripper successfully rotated back and forth and returned to its original position."
