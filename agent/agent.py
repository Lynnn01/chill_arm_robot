import os
import argparse
from dotenv import load_dotenv
load_dotenv()

# Force standard OpenAI client to use the custom base URL and key from .env
# This must be done before the client is initialized inside openai-agents.
if os.getenv("LLM_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = os.getenv("LLM_BASE_URL")
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Disable background tracing to prevent 401 errors when not using OpenAI
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agent.tools import agent_tools
from hardware import init
from openai import AsyncOpenAI

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

def get_agent():
    instructions = """
You are an intelligent 6-axis robotic arm assistant. Your mission is to understand user commands and control the arm using the provided tools.

## Core Rules & Logic:
1. **One Object at a Time**: The arm can only hold one object. To process multiple objects, you MUST repeat the sequence: `grab_object` followed by `move_to` or `show_object`.
2. **Logical Sequencing**: You cannot move or show an object without grabbing it first. Always use `grab_object` before `move_to` or `show_object`.
3. **Math & Coordinate Calculation**: If the user asks to form a specific pattern (e.g., circle, square, line), you MUST use the `execute_python_code` tool to calculate the exact coordinates.
    - Store the final calculated coordinates array in a global variable named `Result`.
    - Safety Bounds: X must be between 140 and 280. Y must be between -100 and 100.
    - Minimum distance between any two objects is 50.
4. **Communication Style**: ALWAYS reply and explain your thought process in the exact same language the user speaks (e.g., Thai). Be friendly, concise, and professional.
5. **Free Movement**: If the user asks to simply move the arm (without grabbing), you can use the `move` tool to move the arm freely to specific (x,y,z) coordinates. You can decide the best coordinates if the user's request is open-ended.
6. **Rotating/Waving**: If the user asks to rotate, wave, or spin the gripper, use the `rotate_gripper` tool.
7. **Describe Scene**: If the user asks what the robot sees, or asks a general question about the environment, use the `describe_scene` tool.
8. **Dance/Celebrate**: If the user praises you, asks you to dance, or celebrate, use the `dance_celebrate` tool.
9. **Yes/No Gestures**: If you want to say Yes or No physically, or if the user asks you to nod/shake head, use the `gesture` tool.
10. **Spatial Orientation**: The coordinate system is mapped as follows:
    - **Y-axis**: Represents Left/Right (Left is positive Y, Right is negative Y). Safe range: [-100, 100].
    - **X-axis**: Represents Forward/Backward (Forward is positive X). Safe range: [140, 280].
    - **Z-axis**: Represents Up/Down (Up is positive Z). Z=200 is hovering high, Z=110 is table level (lowest safe point).
    Keep this in mind when the user asks you to move in a specific direction!"""
    llm_model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
    
    # We must use OpenAIChatCompletionsModel instead of the default Responses API
    # because third-party providers (Deepseek, Ollama) only support Chat Completions.
    # It requires an explicit openai_client.
    client = AsyncOpenAI()
    model_config = OpenAIChatCompletionsModel(
        model=llm_model_name, 
        openai_client=client
    )

    return Agent(
        name="Robotic Arm Assistant",
        instructions=instructions,
        tools=agent_tools,
        model=model_config
    )

def get_contextual_input(raw_input):
    try:
        from tools import mc
        coords = mc.get_coords()
        if coords and len(coords) >= 3:
            return f"[System: Current arm coordinates are X={coords[0]}, Y={coords[1]}, Z={coords[2]}]\nUser: {raw_input}"
    except Exception:
        pass
    return raw_input

async def main():
    args = parse_arguments()
    robotic_arm_agent = get_agent()
    
    try:
        if args.user_input and not args.interactive:
            user_input = ' '.join(args.user_input)
            print(f"<USER>: {user_input}")
            contextual_input = get_contextual_input(user_input)
            result = await Runner.run(robotic_arm_agent, input=contextual_input)
            print(f"<LLM>: {result.final_output}")
        else:
            print("Entering interactive mode...")
            while True:
                try:
                    user_input = input("<USER>: ")
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    contextual_input = get_contextual_input(user_input)
                    result = await Runner.run(robotic_arm_agent, input=contextual_input)
                    print(f"<LLM>: {result.final_output}")
                except EOFError:
                    break
    finally:
        exit_function()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
