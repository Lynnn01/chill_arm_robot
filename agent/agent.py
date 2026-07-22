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
    print(
        "\nProgram is exiting, performing cleanup operations (e.g., returning robot arm to home position)..."
    )
    print("Cleanup complete. Program exited.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Robotic Arm Agent with openai-agents")
    parser.add_argument(
        "user_input",
        nargs="*",
        help="User input content, multiple words will be combined into one sentence",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode, ignore command line input and wait for user input",
    )
    return parser.parse_args()


from agent.prompts import AGENT_SYSTEM_PROMPT

def get_agent():
    instructions = AGENT_SYSTEM_PROMPT
    llm_model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")

    # We must use OpenAIChatCompletionsModel instead of the default Responses API
    # because third-party providers (Deepseek, Ollama) only support Chat Completions.
    # It requires an explicit openai_client.
    # Set explicit timeout to prevent AI requests from hanging indefinitely
    client = AsyncOpenAI(timeout=120.0)
    model_config = OpenAIChatCompletionsModel(
        model=llm_model_name, openai_client=client
    )

    return Agent(
        name="Robotic Arm Assistant",
        instructions=instructions,
        tools=agent_tools,
        model=model_config,
    )


def get_contextual_input(raw_input):
    try:
        from hardware import init

        coords = init.last_coords

        # Format holding status with current held object if any
        if init.is_holding_object:
            held_str = (
                f"'{init.current_held_object}'"
                if init.current_held_object
                else "an unknown object"
            )
            holding_status = f"HOLDING {held_str}"
        else:
            holding_status = "EMPTY (not holding anything)"

        memory_str = f"{init.known_objects}" if init.known_objects else "{}"

        if coords and len(coords) >= 3:
            return f"[System: Current arm coordinates are X={coords[0]}, Y={coords[1]}, Z={coords[2]}. Gripper state: {holding_status}. Known objects in memory: {memory_str}]\nUser: {raw_input}"
    except Exception as e:
        print(f"Context error: {e}")
    return raw_input


async def main():
    args = parse_arguments()
    robotic_arm_agent = get_agent()

    try:
        if args.user_input and not args.interactive:
            user_input = " ".join(args.user_input)
            print(f"<USER>: {user_input}")
            contextual_input = get_contextual_input(user_input)
            result = await Runner.run(robotic_arm_agent, input=contextual_input)
            _process_and_print_result(result.final_output)
        else:
            print("Entering interactive mode...")
            while True:
                try:
                    user_input = input("<USER>: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    contextual_input = get_contextual_input(user_input)
                    result = await Runner.run(robotic_arm_agent, input=contextual_input)
                    _process_and_print_result(result.final_output)
                except EOFError:
                    break
    finally:
        exit_function()


def _play_voice(text, filename="speech.mp3"):
    from agent.tts import play_voice_async
    play_voice_async(text, filename)


def _process_and_print_result(final_output, speaker_on=True):
    import re
    import threading

    voice_text = None
    voice_match = re.search(
        r"<VOICE>(.*?)</VOICE>", final_output, re.DOTALL | re.IGNORECASE
    )
    if voice_match:
        voice_text = voice_match.group(1).strip()
        final_output = re.sub(
            r"<VOICE>.*?</VOICE>", "", final_output, flags=re.DOTALL | re.IGNORECASE
        ).strip()

    print(f"🤖 <LLM>: {final_output}")

    if voice_text and speaker_on:
        threading.Thread(target=_play_voice, args=(voice_text,), daemon=True).start()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
