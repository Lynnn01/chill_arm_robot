import time
from hardware.init import mc
from agents import function_tool

@function_tool
def show_object(object_name: str) -> str:
    """
    Lifts the arm to present the currently grabbed object to the user or camera.
    
    Args:
        object_name: The name of the object being shown.
    """
    print(f"🤖 <SYSTEM>: กำลังโชว์ {object_name}...")
    mc.send_angles([0, 0, 0, 0, 0, -45], 40)
    time.sleep(2)
    mc.send_angles([0, 0, 0, -90, 0, -45], 40)
    time.sleep(2.5)
    return "success"
