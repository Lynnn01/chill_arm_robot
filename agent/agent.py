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
        if init.is_holding_object or init.current_held_object:
            held_str = (
                f"'{init.current_held_object}'"
                if init.current_held_object
                else "an object"
            )
            holding_status = f"HOLDING {held_str} (Notice: If user orders grabbing another object, insert move_to(smart_place=true) first to release this item)"
        else:
            holding_status = "EMPTY (not holding anything)"

        memory_str = f"{init.known_objects}" if init.known_objects else "{}"
        
        # Memory Translator: Detect stacking/blocking relationships
        import armconfig
        blocked_relations = []
        if init.known_objects:
            for obj_a, coord_a in init.known_objects.items():
                if not isinstance(coord_a, list) or len(coord_a) < 2 or coord_a == "in gripper": continue
                if "area" in obj_a.lower() or "zone" in obj_a.lower(): continue
                za = float(coord_a[2]) if len(coord_a) >= 3 and coord_a[2] > 0 else armconfig.GRAB_BASE_HEIGHT
                for obj_b, coord_b in init.known_objects.items():
                    if obj_a == obj_b or not isinstance(coord_b, list) or len(coord_b) < 2 or coord_b == "in gripper": continue
                    if "area" in obj_b.lower() or "zone" in obj_b.lower(): continue
                    zb = float(coord_b[2]) if len(coord_b) >= 3 and coord_b[2] > 0 else armconfig.GRAB_BASE_HEIGHT
                    
                    dx = abs(coord_a[0] - coord_b[0])
                    dy = abs(coord_a[1] - coord_b[1])
                    if dx < getattr(armconfig, "STACK_PROXIMITY_THRESHOLD", 35.0) and dy < getattr(armconfig, "STACK_PROXIMITY_THRESHOLD", 35.0):
                        if zb > za + 10:
                            blocked_relations.append(f"'{obj_a}' is at bottom (blocked by '{obj_b}' on top, use unstack_and_grab)")
                            
        rel_str = ". ".join(blocked_relations)
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
