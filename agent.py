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
from tools import agent_tools
import init
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
    - Safety Bounds: X must be between -70 and 140. Y must be between 150 and 280.
    - Minimum distance between any two objects is 50.
4. **Communication Style**: ALWAYS reply and explain your thought process in the exact same language the user speaks (e.g., Thai). Be friendly, concise, and professional.
    """

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

async def main():
    args = parse_arguments()
    robotic_arm_agent = get_agent()
    
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
