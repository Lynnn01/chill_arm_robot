"""
agent/planner.py — Two-Phase Multitask Planner

Phase 1: Send user input to LLM once, get back a structured JSON task plan.
Phase 2: executor.py runs the tasks locally with zero LLM roundtrips.

Falls back to legacy runner if LLM cannot produce a valid JSON plan
(e.g., for open-ended queries like describe_scene).
"""

import os
import json
import re
import asyncio
from openai import AsyncOpenAI


PLANNER_SYSTEM_PROMPT = """
You are the brain of a 6-axis robotic arm. The user will give you a command.
Your ONLY job is to output a JSON action plan — nothing else.

## JSON FORMAT (strict):
{
  "mode": "plan",
  "plan_summary": "<short Thai description of what you will do>",
  "tasks": [
    {
      "tool": "<tool_name>",
      "args": {<args>},
      "voice": "<1 sentence Isan dialect explanation of what you are doing in this step>"
    },
    ...
  ]
}

## Available tools and their args:
- grab_object(object_name: str, target_coord: list = null)
- move_to(target_coord: list = null, target_name: str = null, target_height: int = 110)
- show_object(object_name: str)
- move(x: float, y: float, z: float, speed: int = 40)
- rotate_gripper(angle_range: int = 45, speed: int = 40)
- dance_celebrate()
- gesture(action: str)   // action = "yes" or "no"
- scan_object(object_name: str)

## Rules:
1. Output ONLY the JSON object. No markdown, no explanation.
2. For sequential tasks (grab then dance, grab then place), list them in order.
3. If placing on another object, use `target_name`. If placing at a specific coordinate, use `target_coord`. If putting it back where it was, leave both null.
4. For commands that need vision/description (e.g. "อธิบายสิ่งที่เห็น"), output: {"mode": "fallback"}
5. For pure conversation (no robot action needed), output: {"mode": "fallback"}
6. You MUST provide a short 'voice' text in Isan dialect (ภาษาอีสาน) for EACH task. This will be spoken WHILE the arm is performing that specific task.

## Coordinate system:
- X: Forward/Backward (Safe: -280 to 280)
- Y: Left/Right, Left=positive (Safe: -280 to 280)
- Z: Height, 200=hover, 110=table (Safe: 0 to 280)
"""

SUMMARY_SYSTEM_PROMPT = """
You are the brain of a 6-axis robotic arm. You have just completed a list of tasks.
The user's original command and the execution results will be provided to you.
You must respond with a natural language summary of what you did.

## Rules:
1. DO NOT use markdown like `**` or `*` for bolding or italics. Use plain text with Emojis.
2. Structure your final output clearly.
3. **CRITICAL: You MUST always respond in Thai language (ภาษาไทย) for your main text response.**
4. **Voice Output**: Always include a short, concise summary (1-2 sentences) of what you did or what you want to say out loud, wrapped in `<VOICE>...</VOICE>` tags at the very end of your response. This text will be spoken by the TTS engine.
5. **CRITICAL: The text inside `<VOICE>` MUST be written in Isan dialect (ภาษาอีสาน) with a cheeky/teasing male persona.** For example: `... <VOICE>จัดให้แล้วเด้อหล่า ย้ายกล่องแดงให้เรียบร้อย บ่อยากสิคุยว่าแม่นปานใด๋</VOICE>`
"""


async def plan_tasks(contextual_input: str) -> dict:
    """
    Call LLM once and get a structured task plan.
    Returns dict with mode="plan" and "tasks" list, or mode="fallback".
    """
    client = AsyncOpenAI(timeout=120.0)
    model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
    raw = ""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user",   "content": contextual_input},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()

        # More robust JSON extraction
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
            
        plan = json.loads(raw)

        if plan.get("mode") not in ("plan", "fallback"):
            return {"mode": "fallback"}

        # Validate plan has tasks
        if plan.get("mode") == "plan":
            tasks = plan.get("tasks", [])
            if not tasks:
                return {"mode": "fallback"}

        return plan

    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"🤖 <SYSTEM>: Planner error ({type(e).__name__}): {e} — falling back to runner")
        if raw:
            print(f"🤖 <SYSTEM>: Raw Output was: {raw[:200]}...")
        return {"mode": "fallback"}

async def summarize_results(contextual_input: str, results: list) -> str:
    """
    Call LLM with the results of the execution to get a conversational summary.
    """
    client = AsyncOpenAI(timeout=120.0)
    model_name = os.getenv("LLM_MODEL_NAME", "deepseek-chat")

    # Format the results into a readable string
    results_str = "Execution Results:\n"
    for r in results:
        results_str += f"- Tool: {r['tool']} | Status: {r['status']} | Result: {r['result']}\n"

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user",   "content": f"{contextual_input}\n\n{results_str}"},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Failed to get summary from LLM: {e}")
        return f"ทำตามคำสั่งเรียบร้อยแล้วครับ แต่ไม่สามารถสร้างสรุปได้ (Error: {e}) <VOICE>เฮ็ดให้แล้วเด้อครับ แต่บ่มีแฮงเว้า</VOICE>"
