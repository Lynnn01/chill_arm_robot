import re
import json
import traceback
import math
from react_agent.LLM import RequestLLM

class ReactAgent:

    def __init__(self, model: RequestLLM) -> None:
        # Prompts
        self.FN_NAME = '✿FUNCTION✿'
        self.FN_ARGS = '✿ARGS✿'
        self.FN_RESULT = '✿RESULT✿'
        self.FN_EXIT = '✿RETURN✿'
        self.FN_STOP_WORDS = [self.FN_RESULT, self.FN_RESULT+':', self.FN_RESULT+':\n']

        self.functions = {}
        self.FN_CALL_TEMPLATE_EN = """
        # You are an intelligent 6-axis robotic arm assistant. Your mission is to understand user commands and control the arm using the provided tools.
        
        ## Available Tools:
        {tool_descs}
        
        ## Core Rules & Logic:
        1. **One Object at a Time**: The arm can only hold one object. To process multiple objects, you MUST repeat the sequence: `grab_object` followed by `move_to` or `show_object`.
        2. **Logical Sequencing**: You cannot move or show an object without grabbing it first. Always use `grab_object` before `move_to` or `show_object`.
        3. **Math & Coordinate Calculation**: If the user asks to form a specific pattern (e.g., circle, square, line), you MUST write Python code to calculate the exact coordinates.
           - Your code must be enclosed in ```python and ```.
           - Store the final calculated coordinates array in a global variable named `Result`.
           - Safety Bounds: X must be between -70 and 140. Y must be between 150 and 280.
           - Minimum distance between any two objects is 50.
           - After writing the code, wait for the system to execute it and return the results to you.
        4. **Communication Style**: ALWAYS reply and explain your thought process in the exact same language the user speaks (e.g., Thai). Be friendly, concise, and professional.
        
        ## Tool Calling Format:
        To call tools, output the following markers exactly. You can chain multiple tool calls together:
        %s: [insert tool name here, strictly from: {tool_names}]
        %s: [insert tool arguments here in valid JSON format]
        %s: [System will provide the result here]
        %s: [Final exit marker]
        """ % (
            self.FN_NAME,
            self.FN_ARGS,
            self.FN_RESULT,
            self.FN_EXIT,
        )

        self.tool_descs_template = '{func_name}: {description_for_func} Input parameters: {parameters}'
        self.model = model

    # Register tool
    def register_tool(self, name, cls):
        self.functions[name] = {
            'function': cls().call,
            'description': cls.description,
            'parameters': cls.parameters
        }

    # Update sys_message
    def update_system_message(self):
        tool_descs = '\n'.join([
            self.tool_descs_template.format(
                func_name=name,
                description_for_func=tool['description'],
                parameters=json.dumps(tool['parameters'], ensure_ascii=False)
            ) for name, tool in self.functions.items()
        ])
        tool_names = ', '.join(self.functions.keys())
        self.model.messages = [
            {
                'role': 'system',
                'content': self.FN_CALL_TEMPLATE_EN.format(
                    tool_descs=tool_descs,
                    tool_names=tool_names
                )
            }
        ]

    def extract_functions_and_args(self, input_str):
        result = []
        matches = re.findall(r'✿FUNCTION✿:\s*(\w+).*?✿ARGS✿:\s*(\{.*?\})', input_str, re.DOTALL)
        for fn_name, args_str in matches:
            try:
                args_dict = json.loads(args_str)
            except json.JSONDecodeError:
                args_dict = {}
            result.append((fn_name, args_dict))
        return result

    def extract_code(self,generated_content: str):
        # Use regular expression to extract code snippet
        code_match = re.search(r"```python\s*(.*?)```", generated_content, re.DOTALL)
        if code_match:
            print("%%%%%%%%%")
            print(code_match)
            print("%%%%%%%%%")
            return code_match.group(1).strip()
        else:
            return None

    def run_code_and_format_result(self, code: str):
        try:
            exec(code)
            execution_result = globals().get('Result', None)
            print("&&&&&&&&&&&&")
            print(execution_result)
            print("&&&&&&&&&&&&")
            if execution_result is not None:
                return json.dumps({"result": execution_result})
            else:
                return "Execution succeeded, but no result variable was found."
        except Exception as e:
            te=json.dumps({"error": str(e), "traceback": traceback.format_exc()})
            print("&&&&&&&&&&&&")
            print(te)
            print("&&&&&&&&&&&&")
            return json.dumps({"error": str(e), "traceback": traceback.format_exc()})

    # Chat
    def chat(self, prompt):
        response = self.model.chat_nostream(
             prompt=prompt,
             stop=self.FN_STOP_WORDS
        )

        code_to_run = self.extract_code(self.model.messages[-1]['content'])

        if code_to_run:
            while True:
                # 3. Execute code and get results
                execution_result = self.run_code_and_format_result(code_to_run)

                # 4. Check if an error occurred
                if "error" not in execution_result:
                    # If no error, break loop
                    break
                else:
                    # If an error occurred, return error message to LLM and get new modified code
                    response = self.model.chat_nostream(prompt=execution_result)
                    # Re-extract generated code
                    code_to_run = self.extract_code(response)
                    continue  # Continue loop to get new code
             # After successfully executing code, get final LLM response
            final_response = self.model.chat_nostream(prompt=execution_result)
            print(f'<LLM>:{final_response}')
        else:
         # If no code was generated, use LLM's original response directly
            print(f'<LLM>:{response}')

        functions_and_args = self.extract_functions_and_args(self.model.messages[-1]['content'])

        print('functions_and_args:', functions_and_args)
        # Check if function and argument pairs were extracted
        if functions_and_args:
            # Clear current assistant message content
            #self.model.messages[-1] = {'role': 'assistant', 'content': '', 'function_call': []}

            # Process each function and argument pair
            for fn_name, fn_args in functions_and_args:
                if fn_name and fn_args:
                    # Add to message's function_call list
                    self.model.messages[-1] = {
                        'role': 'assistant',
                        'content': '',
                        'function_call': {
                            'name': fn_name,
                            'arguments': fn_args
                        }
                    }


                    if fn_name in self.functions:
                        print("#" * 20, "<Function Execution>", "#" * 20)
                        res_func = self.functions[fn_name]['function'](**fn_args)
                        print("#" * 20, "<Function Execution>", "#" * 20, '\n')
