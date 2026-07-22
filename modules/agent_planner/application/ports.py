"""
modules/agent_planner/application/ports.py
Application Layer: Ports (Interfaces) for LLM Task Planning & Execution
"""

from typing import Protocol, Dict, Any
from modules.agent_planner.domain.task_plan import TaskPlan

class LLMPlannerPort(Protocol):
    """Hexagonal Port Interface for LLM Task Planning."""

    async def plan_tasks(self, user_command: str) -> Dict[str, Any]:
        ...

    async def summarize_execution(self, user_command: str, execution_log: list) -> str:
        ...
