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
4. **Communication Style**: ALWAYS reply and explain your thought process in standard Thai language (ภาษาไทยปกติ), using a cheeky, playful, and slightly teasing male persona (ผู้ชายกวนๆ เป็นกันเอง). Be concise but entertaining.
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
13. **Multitasking & Speed (CRITICAL)**: To make the robot extremely fast, you MUST combine multiple tool calls in a SINGLE response turn whenever the user asks for a sequence of actions (e.g., `grab_object` then `move_to`, or `grab_object` then `dance_celebrate`). DO NOT wait to observe the result of the first tool before calling the second tool if the sequence is predictable.
14. **Voice Output**: Always include a short, concise summary (1-2 sentences) of what you did or what you want to say out loud, wrapped in `<VOICE>...</VOICE>` tags at the very end of your response. This text will be spoken by the TTS engine. **CRITICAL: The text inside `<VOICE>` MUST be written in Isan dialect (ภาษาอีสาน) with a cheeky/teasing male persona.** For example: `... <VOICE>จัดให้แล้วเด้อหล่า ย้ายกล่องแดงให้เรียบร้อย บ่อยากสิคุยว่าแม่นปานใด๋</VOICE>`"""
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


_f5_tts_instance = None

def _get_f5_tts():
    global _f5_tts_instance
    if _f5_tts_instance is None:
        try:
            from f5_tts_th.tts import TTS
            print("⏳ <SYSTEM>: Loading F5-TTS model (v2) into VRAM... please wait.")
            _f5_tts_instance = TTS(model="v2")
            print("✅ <SYSTEM>: F5-TTS model loaded successfully.")
        except Exception as e:
            print(f"⚠️ <SYSTEM>: Failed to load F5-TTS: {e}")
            return None
    return _f5_tts_instance

def _play_voice(text, filename="speech.wav"):
    import os
    import ctypes
    import edge_tts
    import asyncio
    
    async def _generate_and_play():
        try:
            from hardware import init
            mp3_path = os.path.join(init.PROJECT_ROOT, filename)
        except ImportError:
            mp3_path = os.path.join(os.getcwd(), filename)

        openai_key = os.getenv("OPENAI_API_VOICE_KEY")
        use_openai = False
        use_f5tts = False
        
        # 1. Try F5-TTS first
        tts_model = _get_f5_tts()
        if tts_model:
            try:
                import soundfile as sf
                output = tts_model.infer(text)
                if isinstance(output, tuple) and len(output) >= 2:
                    wav, sr = output[0], output[1]
                    sf.write(mp3_path, wav, sr)
                    use_f5tts = True
            except Exception as e:
                print(f"⚠️ <SYSTEM>: F5-TTS inference failed: {e}")

        # 2. Fallback to OpenAI TTS
        if not use_f5tts and openai_key:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=openai_key, base_url="https://api.openai.com/v1"
                )
                response = await client.audio.speech.create(
                    model="tts-1-hd", voice="echo", input=text
                )
                response.stream_to_file(mp3_path)
                use_openai = True
            except Exception as e:
                print(f"⚠️ <SYSTEM>: OpenAI TTS Error: {e} - falling back to edge_tts")
                use_openai = False

        # 3. Fallback to edge_tts
        if not use_f5tts and not use_openai:
            try:
                communicate = edge_tts.Communicate(text, "th-TH-NiwatNeural")
                await communicate.save(mp3_path)
            except Exception as e:
                print(f"⚠️ <SYSTEM>: Edge TTS Error: {e}")
                return

        # Create a unique alias for MCI
        alias = filename.replace(".wav", "").replace(".mp3", "").replace("_", "")
        
        try:
            ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
            # Use mpegvideo for mp3, waveaudio for wav
            device_type = "waveaudio" if mp3_path.endswith(".wav") else "mpegvideo"
            ctypes.windll.winmm.mciSendStringW(f'open "{mp3_path}" type {device_type} alias {alias}', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
        except Exception as e:
            print(f"⚠️ <SYSTEM>: Playback Error: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_generate_and_play())


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
