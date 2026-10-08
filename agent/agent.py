import os
import argparse
from dotenv import load_dotenv

load_dotenv(override=True)

# Force standard OpenAI client to use the custom base URL and key from .env
# This must be done before the client is initialized inside openai-agents.
if os.getenv("LLM_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = os.getenv("LLM_BASE_URL")

# Disable background tracing to prevent 401 errors when not using OpenAI
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agent.tools import agent_tools
from hardware import init
from openai import AsyncOpenAI


def exit_function():
    """Cleanup function executed upon program exit"""
    try:
        from hardware import init
        print("\n🤖 <SYSTEM>: กำลังคลายล็อกเซอร์โวมอเตอร์เพื่อความปลอดภัยก่อนปิดโปรแกรม...")
        init.mc.release_all_servos()
    except Exception as e:
        print(f"Cleanup error: {e}")
    print("✅ <SYSTEM>: ออกจากโปรแกรมเรียบร้อย")


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
    llm_model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

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


def _holding_status() -> str:
    """Gripper state text for the LLM context (init.* flags)."""
    if init.is_holding_object or init.current_held_object:
        held_str = (
            f"'{init.current_held_object}'"
            if init.current_held_object
            else "an object"
        )
        return f"HOLDING {held_str} (Notice: Gripper is currently holding an item. If user asks to place/release it, OR orders ANY action requiring free hands such as grabbing another object, gestures, dancing, rock-paper-scissors, or sorting, you MUST insert move_to(smart_place=true) as the FIRST step to place down what is in hand before performing that action)"
    return "EMPTY (not holding anything)"


def _blocked_relations(known_objects: dict) -> list:
    """Memory Translator: describe which remembered objects are buried under another."""
    import armconfig
    threshold = getattr(armconfig, "STACK_PROXIMITY_THRESHOLD", 35.0)

    def _placed(name, coord):
        return (
            isinstance(coord, list) and len(coord) >= 2 and coord != "in gripper"
            and "area" not in name.lower() and "zone" not in name.lower()
        )

    def _z(coord):
        return float(coord[2]) if len(coord) >= 3 and coord[2] > 0 else armconfig.GRAB_BASE_HEIGHT

    relations = []
    for obj_a, coord_a in known_objects.items():
        if not _placed(obj_a, coord_a):
            continue
        za = _z(coord_a)
        for obj_b, coord_b in known_objects.items():
            if obj_a == obj_b or not _placed(obj_b, coord_b):
                continue
            zb = _z(coord_b)
            dx = abs(coord_a[0] - coord_b[0])
            dy = abs(coord_a[1] - coord_b[1])
            if dx < threshold and dy < threshold and zb > za + 10:
                relations.append(f"'{obj_a}' is at bottom (blocked by '{obj_b}' on top, use unstack_and_grab)")
    return relations


def get_contextual_input(raw_input):
    try:
        coords = init.last_coords
        holding_status = _holding_status()
        memory_str = f"{init.known_objects}" if init.known_objects else "{}"

        rel_str = ". ".join(_blocked_relations(init.known_objects)) if init.known_objects else ""
        if rel_str:
            memory_str += f" | Logical insights: {rel_str}"

        coord_str = f"X={coords[0]}, Y={coords[1]}, Z={coords[2]}" if (coords and len(coords) >= 3) else "Unknown"
        return f"[System: Current arm coordinates are {coord_str}. Gripper state: {holding_status}. Known objects in memory: {memory_str}]\nUser: {raw_input}"
    except Exception as e:
        print(f"Context error: {e}")
    return raw_input


async def process_user_input(user_input: str, agent, speaker_on: bool = True):
    from agent.planner import plan_tasks, summarize_results
    from agent.executor import execute_plan
    
    contextual_input = get_contextual_input(user_input)
    
    # ── Phase 1: Plan ──────────────────────────────
    plan = await plan_tasks(contextual_input)



    if plan.get("mode") == "plan":
        # ── Phase 2: Execute (zero roundtrips) ─────
        results = execute_plan(
            tasks=plan.get("tasks", []),
            plan_summary=plan.get("plan_summary", ""),
            speaker_on=speaker_on,
        )
        
        # ── Phase 3: Summarize ─────────────────────
        print("🤖 <SYSTEM>: กำลังสรุปผลการทำงาน...")
        final_summary = await summarize_results(contextual_input, results)
        print("\n", end="")
        _process_and_print_result(final_summary, speaker_on=speaker_on)
        print("\n", end="")
    else:
        # ── Fallback: legacy Runner ─────────────────
        print("🤖 <SYSTEM>: ใช้ Runner ปกติ (fallback mode)...")
        result = await Runner.run(agent, input=contextual_input)
        print("\n", end="")
        _process_and_print_result(result.final_output, speaker_on=speaker_on)
        print("\n", end="")


async def main():
    args = parse_arguments()
    robotic_arm_agent = get_agent()

    try:
        if args.user_input and not args.interactive:
            user_input = " ".join(args.user_input)
            print(f"<USER>: {user_input}")
            await process_user_input(user_input, robotic_arm_agent)
        else:
            print("Entering interactive mode...")
            while True:
                try:
                    user_input = input("<USER>: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    await process_user_input(user_input, robotic_arm_agent)
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
