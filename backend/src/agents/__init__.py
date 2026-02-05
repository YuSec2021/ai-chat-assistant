"""Agents package"""

from src.agents.base import BaseAgent, AgentRegistry, agent_registry
from src.agents.supervisor import SupervisorAgent
from src.agents.financial import FinancialAnalysisAgent
from src.agents.document import DocumentAnalysisAgent

# Register all agents
agent_registry.register(SupervisorAgent())
agent_registry.register(FinancialAnalysisAgent())
agent_registry.register(DocumentAnalysisAgent())

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "agent_registry",
    "SupervisorAgent",
    "FinancialAnalysisAgent",
    "DocumentAnalysisAgent",
]
