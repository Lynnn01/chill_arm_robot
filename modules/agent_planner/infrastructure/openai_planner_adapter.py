"""
modules/agent_planner/infrastructure/openai_planner_adapter.py
Infrastructure Layer: Adapter implementing LLMPlannerPort using agent.planner
"""

from typing import Dict, Any
from agent.planner import plan_tasks, summarize_execution
from modules.agent_planner.application.ports import LLMPlannerPort

class OpenAIPlannerAdapter(LLMPlannerPort):
    """Adapter for LLM Task Planning."""

    async def plan_tasks(self, user_command: str) -> Dict[str, Any]:
        return await plan_tasks(user_command)

    async def summarize_execution(self, user_command: str, execution_log: list) -> str:
        return await summarize_execution(user_command, execution_log)
