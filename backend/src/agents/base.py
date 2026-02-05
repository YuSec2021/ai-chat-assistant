"""Base Agent class and Agent registry"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.models.conversation import AgentInfo
import structlog

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.category = "general"

    @abstractmethod
    async def execute(
        self,
        input_text: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Execute the agent's task"""
        pass

    def get_info(self) -> AgentInfo:
        """Get agent information"""
        return AgentInfo(
            name=self.name,
            description=self.description,
            category=self.category
        )


class AgentRegistry:
    """Registry for managing agents"""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Register an agent"""
        self._agents[agent.name] = agent
        logger.info("Agent registered", name=agent.name)

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self._agents.get(name)

    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents"""
        return [agent.get_info() for agent in self._agents.values()]

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered"""
        return name in self._agents


# Global agent registry
agent_registry = AgentRegistry()
