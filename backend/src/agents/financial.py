"""Financial Analysis Agent - Specialized for financial data and market analysis"""

from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.core.llm_client import get_llm_response
import structlog

logger = structlog.get_logger(__name__)


class FinancialAnalysisAgent(BaseAgent):
    """Financial analysis agent for market data and financial queries"""

    def __init__(self):
        super().__init__()
        self.name = "FinancialAnalysis"
        self.description = "Specialized agent for financial market analysis, stock prices, cryptocurrency data, and trading signals"
        self.category = "financial"

    async def execute(
        self,
        input_text: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Execute financial analysis task"""

        system_prompt = """You are a Financial Analysis Agent specialized in:
- Stock market analysis
- Cryptocurrency price tracking and analysis
- Market sentiment analysis
- Financial data interpretation
- Trading signals and technical analysis (educational only)

Provide clear, well-structured financial insights. Always include appropriate disclaimers that this is not financial advice.

For real-time data queries, if you don't have access to current data, let the user know and suggest what data they should provide.

Format your responses in Markdown with:
- Clear sections
- Data tables when appropriate
- Bullet points for key insights
- Risk warnings where applicable"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ]

        try:
            response = await get_llm_response(messages)
            return response

        except Exception as e:
            logger.error("Financial analysis failed", error=str(e))
            return f"I apologize, but I encountered an error while analyzing the financial data: {str(e)}"
