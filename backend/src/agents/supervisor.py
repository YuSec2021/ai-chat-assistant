"""Supervisor Agent - Main intent recognition and routing agent"""

import json
from typing import Dict, Any, Optional, List
from src.agents.base import BaseAgent, agent_registry
from src.core.llm_client import get_llm_response
from src.models.conversation import IntentResult
import structlog

logger = structlog.get_logger(__name__)


class SupervisorAgent(BaseAgent):
    """Supervisor agent for intent recognition and routing"""

    def __init__(self):
        super().__init__()
        self.name = "Supervisor"
        self.description = "Main agent that recognizes user intent and routes to appropriate specialized agents"
        self.category = "supervisor"

    async def recognize_intent(
        self,
        user_message: str,
        context: Dict[str, Any] = None
    ) -> IntentResult:
        """Recognize user intent using LLM"""

        # Get available agents
        available_agents = agent_registry.list_agents()
        agent_list = "\n".join([
            f"- {agent.name}: {agent.description} (category: {agent.category})"
            for agent in available_agents
            if agent.name != "Supervisor"
        ])

        system_prompt = f"""You are the Supervisor agent for an AI assistant. Your role is to:

1. Analyze the user's message and understand their intent
2. Decide which specialized agent should handle this request, or if it should be handled directly by the main LLM
3. Return your decision as JSON

Available specialized agents:
{agent_list}

Categories:
- financial: Market analysis, stock prices, financial data, trading signals
- document: PDF/Excel analysis, document processing, data extraction
- general: General chat, questions, creative writing (no special agent needed)

Return a JSON object with this exact format:
{{
    "intent": "specific_intent_name",
    "confidence": 0.0-1.0,
    "agent": "AgentName or null",
    "reasoning": "brief explanation"
}}

Examples:
User: "What's the price of Bitcoin?"
Response: {{"intent": "crypto_price_query", "confidence": 0.95, "agent": "FinancialAnalysis", "reasoning": "User is asking for cryptocurrency pricing information"}}

User: "Summarize this PDF report"
Response: {{"intent": "document_summary", "confidence": 0.9, "agent": "DocumentAnalysis", "reasoning": "User wants to summarize a PDF document"}}

User: "Tell me a joke"
Response: {{"intent": "general_chat", "confidence": 0.9, "agent": null, "reasoning": "General conversation request, no specialized agent needed"}}
"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            response = await get_llm_response(messages)

            # Parse JSON response
            result_data = json.loads(response)

            return IntentResult(**result_data)

        except Exception as e:
            logger.error("Intent recognition failed", error=str(e))
            # Default to general chat
            return IntentResult(
                intent="general_chat",
                confidence=0.5,
                agent=None,
                reasoning="Intent recognition failed, defaulting to general chat"
            )

    async def execute(
        self,
        input_text: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Execute supervisor task - delegate to appropriate agent"""

        # Recognize intent
        intent_result = await self.recognize_intent(input_text, context)

        logger.info(
            "Intent recognized",
            intent=intent_result.intent,
            agent=intent_result.agent,
            confidence=intent_result.confidence
        )

        # Route to specialized agent if needed
        if intent_result.agent and agent_registry.has_agent(intent_result.agent):
            agent = agent_registry.get(intent_result.agent)
            return await agent.execute(input_text, context)

        # Handle directly with LLM
        messages = context.get("messages", [])
        messages.append({"role": "user", "content": input_text})

        response = await get_llm_response(messages)
        return response
