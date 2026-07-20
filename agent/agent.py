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
    - Safety Bounds: X must be between -280 and 280. Y must be between -280 and 280.
    - Minimum distance between any two objects is 50.
4. **Communication Style**: ALWAYS reply and explain your thought process in the exact same language the user speaks (e.g., Thai). Be friendly, concise, and professional.
5. **Free Movement**: If the user asks to simply move the arm (without grabbing), you can use the `move` tool to move the arm freely to specific (x,y,z) coordinates. You can decide the best coordinates if the user's request is open-ended.
6. **Rotating/Waving**: If the user asks to rotate, wave, or spin the gripper, use the `rotate_gripper` tool.
7. **Describe Scene**: If the user asks what the robot sees, or asks a general question about the environment, use the `describe_scene` tool.
8. **Dance/Celebrate**: If the user praises you, asks you to dance, or celebrate, use the `dance_celebrate` tool.
9. **Yes/No Gestures**: If you want to say Yes or No physically, or if the user asks you to nod/shake head, use the `gesture` tool.
10. **Spatial Orientation**: The coordinate system is mapped as follows:
    - **Y-axis**: Represents Left/Right (Left is positive Y, Right is negative Y). Safe range: [-280, 280].
    - **X-axis**: Represents Forward/Backward (Forward is positive X). Safe range: [-280, 280].
    - **Z-axis**: Represents Up/Down (Up is positive Z). Z=200 is hovering high, Z=110 is table level (lowest safe point). Safe range: [0, 280].
    Keep this in mind when the user asks you to move in a specific direction!
11. **Object Memory**: You can use the `scan_object` tool to search the environment and remember an object's location. If the system context shows an object is already in "Known objects", you can use `grab_object` directly without needing to provide `target_coord` (it will pull from memory automatically).
12. **Response Formatting**: DO NOT use markdown like `**` or `*` for bolding or italics because the UI does not support it. Use clear, plain text with Emojis to make it readable. Instead of markdown, use clean bullet points like `- ` or `1. ` and use spaces/newlines to separate thoughts. Structure your final output clearly so the user can easily read it.
13. **Voice Output**: Always include a short, concise summary (1-2 sentences) of what you did or what you want to say out loud, wrapped in `<VOICE>...</VOICE>` tags at the very end of your response. This text will be spoken by the TTS engine. **CRITICAL: The text inside `<VOICE>` MUST be written in Isan dialect (ภาษาอีสาน) playfully and naturally.** For example: `... <VOICE>หยิบกล่องสีแดงให้เรียบร้อยแล้วเด้อจ้า สิจัดให้ตามคำขอเลย</VOICE>`"""
    llm_model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
    
    # We must use OpenAIChatCompletionsModel instead of the default Responses API
    # because third-party providers (Deepseek, Ollama) only support Chat Completions.
    # It requires an explicit openai_client.
    # Set explicit timeout to prevent AI requests from hanging indefinitely
    client = AsyncOpenAI(timeout=120.0)
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
        from hardware import init
        coords = init.last_coords
        
        # Format holding status with current held object if any
        if init.is_holding_object:
            held_str = f"'{init.current_held_object}'" if init.current_held_object else "an unknown object"
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
            user_input = ' '.join(args.user_input)
            print(f"<USER>: {user_input}")
            contextual_input = get_contextual_input(user_input)
            result = await Runner.run(robotic_arm_agent, input=contextual_input)
            _process_and_print_result(result.final_output)
        else:
            print("Entering interactive mode...")
            while True:
                try:
                    user_input = input("<USER>: ")
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    contextual_input = get_contextual_input(user_input)
                    result = await Runner.run(robotic_arm_agent, input=contextual_input)
                    _process_and_print_result(result.final_output)
                except EOFError:
                    break
    finally:
        exit_function()

def _play_voice(text):
    try:
        from openai import OpenAI
        import subprocess
        
        # Create a sync client. It will automatically use OPENAI_API_KEY from environment.
        sync_client = OpenAI()
        
        # Some custom endpoints (like DeepSeek) might not support TTS.
        # We attempt to use the standard OpenAI TTS.
        response = sync_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="wav"
        )
        wav_path = os.path.join(init.PROJECT_ROOT, "speech.wav")
        response.stream_to_file(wav_path)
        
        # Play asynchronously using Windows built-in winsound
        import winsound
        winsound.PlaySound(wav_path, winsound.SND_FILENAME)
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Voice TTS Error: {e}")

def _process_and_print_result(final_output):
    import re
    import threading
    
    voice_text = None
    voice_match = re.search(r'<VOICE>(.*?)</VOICE>', final_output, re.DOTALL | re.IGNORECASE)
    if voice_match:
        voice_text = voice_match.group(1).strip()
        final_output = re.sub(r'<VOICE>.*?</VOICE>', '', final_output, flags=re.DOTALL | re.IGNORECASE).strip()
        
    print(f"<LLM>: {final_output}")
    
    if voice_text:
        threading.Thread(target=_play_voice, args=(voice_text,), daemon=True).start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
