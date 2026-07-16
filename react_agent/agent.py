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
        # You are my robotic arm assistant, helping me control a 6-axis robotic arm. The arm has built-in functions, please output the corresponding functions to execute according to my instructions and the requirements below.
        ## You have the following tools:
        {tool_descs}
        ## move_to is used to move objects to specified positions to form a specific pattern, show_object is used to display objects, and grab_object is used to find and grab a specified object. You must first use the grab_object tool, followed immediately by either the move_to or show_object tool.
        ## All tools can only handle one object at a time, so when you need to handle multiple objects, you need to repeat grab_object and move_to or show_object!
        ## You can insert zero, one, or multiple of the following commands in your reply to call tools, and finally return to the initial position. If you need a loop, you can call the same tool multiple times; if you need to implement multiple functions in a command, you can also call multiple tools in sequence. The order in which tool functions appear represents the order of execution.
        ## Here are some examples:
            One: My instruction: "Grab two red blocks, show one to me, and put the other in an arbitrary position".
            You output: "
✿FUNCTION✿: grab_object
✿FUNCTION✿: show_object
✿FUNCTION✿: grab_object
✿FUNCTION✿: move_to
✿ARGS✿: {{"object_name": "red block"}}
✿ARGS✿: {{"object_name": "red block"}}
✿ARGS✿: {{"object_name": "red block"}}
✿ARGS✿: {{"target_coord": [-80,200]}}
"; Because I need two red blocks, you need to execute grab_object twice consecutively, the first time use show_object to show me, the second time use Move_to to move to the specified position. The logic for other instructions is similar.
Two: My instruction: "Use eight blocks to form a circle, use code to calculate precise coordinates".
Here, the specified pattern is explicitly requested in the instruction, and it requires calculating coordinates with code. Therefore, first you need to write a complete python code, which can be run directly and returns coordinate results, and according to the pattern required in the instruction, calculates the precise coordinates of each point. The X coordinate range of all points is -70 to 140, the Y coordinate range is 150 to 280, "the distance between any two adjacent points is not less than 50", absolutely cannot exceed the range! The results must be stored in the global variable 'Result'! Then wait for me to help you execute the code to get the results, and then provide tool parameters based on the results I give you.
        # Only when the instruction explicitly asks to write code, then use code to calculate coordinates! Code should be placed between "```python" and "```" strings for easy extraction.
        %s: Tool name, if using a tool it must be one of [{tool_names}], the name of the tool must not be modified or translated!
        %s: Tool inputs, in json format!
        %s: Tool result.
        %s: You must reply using the user's language (Chinese or other languages) based on the tool result""" % (
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

    # Remove special characters
    def remove_special_tokens(self, text, strip=True):
        text = text.replace('✿:', '✿')
        text = text.replace('✿：', '✿')
        out = ''
        is_special = False
        for c in text:
            if c == '✿':
                is_special = not is_special
                continue
            if is_special:
                continue
            out += c
        if strip:
            out = out.lstrip('\n').rstrip()
        return out

    def extract_functions_and_args(self,input_str):
        # Initialize result list
        result = []

        # Use regular expression to find all function name and argument pairs
        function_matches = re.findall(r'✿FUNCTION✿:\s*(\w+)', input_str)
        args_matches = re.findall(r'✿ARGS✿:\s*(\{.*?\})', input_str, re.DOTALL)

        # Iterate through matched function name and argument pairs, and parse arguments
        for i in range(len(function_matches)):
            function_name = function_matches[i]
            args_str = args_matches[i]

            try:
                # Parse argument string to dictionary
                args_dict = json.loads(args_str)
            except json.JSONDecodeError:
                args_dict = {}

            result.append((function_name, args_dict))


        return result
    
    def stream_output(self, response):
        for chunk in response:
            print(chunk, flush=True, end='')
        print()

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
            print('<LLM>:', end='')
            self.stream_output(final_response)
        else:
         # If no code was generated, use LLM's original response directly
            print('<LLM>:', end='')
            self.stream_output(response)

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

                        '''
                        response = self.model.chat_stream(
                            prompt="""
                                ✿FUNCTION✿: {fn_name}
                                ✿ARGS✿: {fn_args}
                                ✿RESULT✿: {res_func}
                                ✿RETURN✿
                            """.format(fn_name=fn_name, fn_args=fn_args, res_func=res_func),
                        )
                        self.stream_output(response)
'''
