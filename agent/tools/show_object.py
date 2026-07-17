import time
from hardware.init import mc
from agents import function_tool

@function_tool
def show_object(object_name: str) -> str:
    """
    [Tags: Action, Interaction]
    Lifts the arm to present the currently grabbed object to the user or camera.
    
    When to use:
    - เมื่อถือของอยู่ แล้วผู้ใช้สั่งว่า "เอามาดูหน่อย", "โชว์ให้ดูหน่อย", "ยกขึ้นมา" เพื่อให้คนเห็นชัดๆ
    - ห้ามใช้ถ้าในมือยังไม่ได้ถืออะไรอยู่
    
    Args:
        object_name: The name of the object being shown.
    """
    print(f"🤖 <SYSTEM>: กำลังโชว์ {object_name}...")
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(2)
    mc.send_angles([0, 0, 0, -90, 0, -45], 40)
    time.sleep(2.5)
    return "success"
