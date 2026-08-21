from agent.tools.shares._raw import raw_describe_scene
from agents import function_tool

@function_tool
def describe_scene(question: str) -> str:
    """
    [Tags: Vision, Analysis]
    Takes a photo using the robot's camera and asks the vision model to describe the scene or answer a specific question about it.
    
    When to use:
    - เมื่อผู้ใช้ถามว่า "เห็นอะไรบ้าง", "มีอะไรอยู่บนโต๊ะ", "อธิบายสิ่งที่อยู่ตรงหน้า"
    - ใช้เพื่อตอบคำถามกว้างๆ โดยไม่ต้องระบุชื่อวัตถุ (ต่างจาก scan_object ที่หาเฉพาะเจาะจง)
    
    Args:
        question: The specific question to ask about the scene. E.g., "What objects are on the table?", "Do you see a person?", "What color is the block?"
    """
    res = raw_describe_scene(question)
    if isinstance(res, dict):
        return f"Vision Model Description:\n{res.get('result', res.get('message', ''))}"
    return str(res)

