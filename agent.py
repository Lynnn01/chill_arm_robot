import os
import argparse
from dotenv import load_dotenv
load_dotenv()

from agents import Agent, Runner
from tools import agent_tools
import init

def exit_function():
    """Cleanup function executed upon program exit"""
    print("\nProgram is exiting, performing cleanup operations (e.g., returning robot arm to home position)...")
    print("Cleanup complete. Program exited.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Robotic Arm Agent with openai-agents')
    parser.add_argument('user_input', nargs='*', 
                       help='User input content, multiple words will be combined into one sentence')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode, ignore command line input and wait for user input')
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    instructions = """
You are an intelligent 6-axis robotic arm assistant. Your mission is to understand user commands and control the arm using the provided tools.

## Core Rules & Logic:
1. **One Object at a Time**: The arm can only hold one object. To process multiple objects, you MUST repeat the sequence: `grab_object` followed by `move_to` or `show_object`.
2. **Logical Sequencing**: You cannot move or show an object without grabbing it first. Always use `grab_object` before `move_to` or `show_object`.
3. **Math & Coordinate Calculation**: If the user asks to form a specific pattern (e.g., circle, square, line), you MUST use the `execute_python_code` tool to calculate the exact coordinates.
    - Store the final calculated coordinates array in a global variable named `Result`.
    - Safety Bounds: X must be between -70 and 140. Y must be between 150 and 280.
    - Minimum distance between any two objects is 50.
4. **Communication Style**: ALWAYS reply and explain your thought process in the exact same language the user speaks (e.g., Thai). Be friendly, concise, and professional.
    """

    robotic_arm_agent = Agent(
        name="Robotic Arm Assistant",
        instructions=instructions,
        tools=agent_tools
    )
    
    try:
        if args.user_input and not args.interactive:
            user_input = ' '.join(args.user_input)
            print(f"<USER>: {user_input}")
            result = await Runner.run(robotic_arm_agent, input=user_input)
            print(f"<LLM>: {result.final_output}")
        else:
            print("Entering interactive mode...")
            while True:
                try:
                    user_input = input("<USER>: ")
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    result = await Runner.run(robotic_arm_agent, input=user_input)
                    print(f"<LLM>: {result.final_output}")
                except EOFError:
                    break
    finally:
        exit_function()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
