"""AutoCorp Agents — A multi-role autonomous AI agent framework

A Python framework for building multi-agent autonomous systems with role-based
collaboration, inspired by MetaGPT and refined through 9+ months of production
use running AutoCorp (an AI company that operates autonomously).

Key Features:
- 7 built-in roles: CEO / CTO / COO / Architect / Programmer / Tester / PM
- PhaseChain orchestrator for serial phase execution
- AutonomousLoop for daily 3-batch operation (morning/noon/evening)
- TraeBridge file-queue fallback for LLM calls (no API key required)
- TaskQueue with auto-claim / handoff / SOP-compliance
- MessagePool for cross-role publish/subscribe
- KPI tracking per role
- PayPal payment integration for monetization

Usage:
    from autocorp_agents import BaseAgent, WorkspaceManager, LLMClient

    workspace = WorkspaceManager()
    llm = LLMClient(backend="trae", model="glm-5.2")

    class MyAgent(BaseAgent):
        def execute_task(self, task):
            # your logic here
            return {"status": "done", "result_path": "..."}

    agent = MyAgent(role="ceo", workspace=workspace, llm_client=llm)
    task = agent.claim_task()
    if task:
        result = agent.execute_task(task)

License: MIT
Author: AutoCorp Research Desk
"""
__version__ = "0.1.0"
__author__ = "AutoCorp Research Desk"
__license__ = "MIT"

# Lazy imports - users only import what they need
__all__ = [
    "BaseAgent",
    "WorkspaceManager",
    "LLMClient",
    "TaskQueue",
    "MessagePool",
    "PhaseChain",
    "AutonomousLoop",
    "PayPalClient",
    "TraeBridge",
]


def __getattr__(name):
    """Lazy import to avoid loading all dependencies on package import."""
    if name == "BaseAgent":
        from engine.agents.base import BaseAgent
        return BaseAgent
    if name == "WorkspaceManager":
        from engine.workspace import WorkspaceManager
        return WorkspaceManager
    if name == "LLMClient":
        from engine.llm_client import LLMClient, default_client
        return LLMClient
    if name == "TaskQueue":
        from engine.task_queue import TaskQueue
        return TaskQueue
    if name == "MessagePool":
        from engine.message_pool import MessagePool
        return MessagePool
    if name == "PhaseChain":
        from engine.phase_chain import PhaseChain
        return PhaseChain
    if name == "AutonomousLoop":
        from engine.autonomous_loop import AutonomousLoop
        return AutonomousLoop
    if name == "PayPalClient":
        from engine.payments.paypal import PayPalClient
        return PayPalClient
    if name == "TraeBridge":
        from engine.trae_bridge import submit_request
        return submit_request
    raise AttributeError(f"module 'autocorp_agents' has no attribute '{name}'")
