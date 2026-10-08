from agents import function_tool
from agent.tools.shares._raw import raw_move_around

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
    raw_move_around(speed)
    return "Arm successfully moved around the environment."
