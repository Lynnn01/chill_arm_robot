import traceback
import json
from agents import function_tool

@function_tool
def execute_python_code(code: str) -> str:
    """
    Executes Python code to calculate coordinates for complex patterns (e.g., circle, square, shapes).
    The code must store the final calculated coordinates array in a global variable named 'Result'.
    
    Args:
        code: The Python code to execute.
    """
    try:
        exec_globals = {}
        exec(code, exec_globals)
        execution_result = exec_globals.get('Result', None)
        print("&&&&&&&&&&&&")
        print(execution_result)
        print("&&&&&&&&&&&&")
        if execution_result is not None:
            return json.dumps({"result": execution_result})
        else:
            return "Execution succeeded, but no 'Result' variable was found."
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})
