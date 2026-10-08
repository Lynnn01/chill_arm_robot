from agents import function_tool
from agent.tools.shares._raw import raw_give_to_person

@function_tool
def give_to_person() -> str:
    """
    [Tags: Action, Interaction]
    Hands over the currently held object to a person. It extends the arm forward and releases the object after 4 seconds.
    
    When to use:
    - เมื่อผู้ใช้สั่งให้ "ส่งของให้ฉันหน่อย", "เอามาให้ฉัน", "ยื่นให้หน่อย"
    - ต้องเรียกใช้ **หลังจาก** ใช้ grab_object หยิบของสำเร็จแล้วเท่านั้น ห้ามใช้ถ้ามือเปล่า
    - ห้ามใช้คำสั่งนี้เด็ดขาดถ้าผู้ใช้แค่สั่งให้ "วาง", "โชว์", หรือถ้าเป็นโหมด Auto แล้วไม่มีใครอยู่รับของ
    """
    result = raw_give_to_person()
    if isinstance(result, dict) and result.get("status") == "ERROR":
        return f"Error: {result.get('message', 'Unknown error')}"
    return "Handover completed. Object released to the person."
