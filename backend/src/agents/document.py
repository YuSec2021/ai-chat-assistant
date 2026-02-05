"""Document Analysis Agent - Specialized for PDF, Excel and document processing"""

from typing import Dict, Any, List
from pathlib import Path
from src.agents.base import BaseAgent
from src.services.document import DocumentService
from src.core.llm_client import get_llm_response
import structlog

logger = structlog.get_logger(__name__)


class DocumentAnalysisAgent(BaseAgent):
    """Document analysis agent for PDF, Excel and other document types"""

    def __init__(self):
        super().__init__()
        self.name = "DocumentAnalysis"
        self.description = "Specialized agent for analyzing PDF documents, Excel spreadsheets, and extracting structured data from various file formats"
        self.category = "document"
        self.doc_service = DocumentService()

    async def execute(
        self,
        input_text: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Execute document analysis task"""

        context = context or {}
        attachment_ids = context.get("attachments", [])

        system_prompt = """You are a Document Analysis Agent specialized in:
- Analyzing PDF documents and extracting key information
- Processing Excel spreadsheets and performing data analysis
- Summarizing document contents
- Extracting structured data from unstructured documents
- Answering questions about document content

Provide clear, well-structured analysis in Markdown format with:
- Executive summary
- Key findings
- Data tables when appropriate
- Insights and recommendations
- References to specific parts of the document"""

        # Process attachments if present
        document_content = ""
        if attachment_ids:
            for file_id in attachment_ids:
                try:
                    content = await self.doc_service.process_file(file_id)
                    document_content += f"\n\n--- Document Content ({file_id}) ---\n{content}\n--- End of Document ---\n"
                except Exception as e:
                    logger.error("Document processing failed", file_id=file_id, error=str(e))
                    document_content += f"\n\nError processing document {file_id}: {str(e)}\n"

        # Combine user query with document content
        full_input = input_text
        if document_content:
            full_input = f"User Query: {input_text}\n\nDocument Content:\n{document_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_input}
        ]

        try:
            response = await get_llm_response(messages)
            return response

        except Exception as e:
            logger.error("Document analysis failed", error=str(e))
            return f"I apologize, but I encountered an error while analyzing the document: {str(e)}"
