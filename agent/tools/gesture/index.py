from agents import function_tool
from agent.tools.shares._raw import raw_gesture

@function_tool
def gesture(action: str) -> str:
    """
    [Tags: Action, Interaction]
    Performs a gesture ("yes" or "no") by nodding or shaking the arm.
    
    When to use:
    - เมื่อต้องการตอบสนองผู้ใช้แบบ non-verbal เช่น ผู้ใช้ถามว่า "พร้อมไหม?", "ทำได้ไหม?"
    - "yes" = ผงกหัว (พยักหน้า) รับทราบ หรือเห็นด้วย
    - "no" = ส่ายหัวปฏิเสธ หรือแสดงว่าทำไม่ได้
    
    Args:
        action: The gesture to perform. Must be either 'yes' or 'no'.
    """
    result = raw_gesture(action)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return f"Performed gesture {action} successfully."
            
    return f"Performed gesture {action} successfully."
