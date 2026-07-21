from agents import function_tool
from agent.tools.shares._raw import raw_scan_object

@function_tool
def scan_object(object_name: str) -> str:
    """
    [Tags: Vision, Memory, Search]
    Uses the camera to scan the environment for a specific object.
    If found, the AI will remember its coordinates for future use.
    
    When to use: 
    - เมื่อผู้ใช้ถามหาตำแหน่งของสิ่งของ หรือสั่งให้มองหา/สแกนหาสิ่งของ
    - ห้ามใช้ถ้าผู้ใช้สั่งให้ "หยิบ" (ใช้ grab_object แทน)
    
    Args:
        object_name: The descriptive name of the object to search for (e.g., "red block").
    """
    result = raw_scan_object(object_name)
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return result.get("message", f"Found '{object_name}'. Memory updated.")
            
    return f"Found '{object_name}'. Memory updated."
