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
from agent.prompts import PLANNER_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT


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
            max_tokens=1536,
        )
        raw = response.choices[0].message.content.strip()

        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\n?```$", "", raw, flags=re.MULTILINE).strip()

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
