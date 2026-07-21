from agents import function_tool
from agent.tools.shares._raw import raw_dance_celebrate

@function_tool
def dance_celebrate() -> str:
    """
    [Tags: Action, Interaction]
    Makes the robotic arm perform a short, pre-programmed dance sequence to celebrate success.
    
    When to use:
    - เมื่อผู้ใช้บอกให้ "เต้นหน่อย", "ฉลองหน่อย", "ดีใจด้วย" 
    - หรือหลังจากทำภารกิจชุดใหญ่/ภารกิจที่ยากสำเร็จ (เช่น หยิบและเรียงของเสร็จสมบูรณ์ 3 ชิ้น)
    """
    result = raw_dance_celebrate()
    
    if isinstance(result, dict):
        if result.get("status") == "ERROR":
            return f"Error: {result.get('message', 'Unknown error')}"
        elif result.get("status") == "DONE TASK":
            return "Dance completed successfully."
            
    return "Dance completed successfully."
