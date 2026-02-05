"""Document processing service for PDF, Excel, and other file types"""

import io
import pandas as pd
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Optional
from src.utils.temp_manager import temp_manager
import structlog

logger = structlog.get_logger(__name__)


class DocumentService:
    """Service for processing various document types"""

    async def process_file(self, file_id: str) -> str:
        """Process a file and return its text content"""

        file_path = temp_manager.get_temp_path(file_id)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")

        file_ext = file_path.suffix.lower()

        try:
            if file_ext == ".pdf":
                return await self._process_pdf(file_path)
            elif file_ext in [".xlsx", ".xls"]:
                return await self._process_excel(file_path)
            elif file_ext == ".csv":
                return await self._process_csv(file_path)
            elif file_ext in [".txt", ".md", ".json"]:
                return await self._process_text(file_path)
            else:
                return f"[Unsupported file type: {file_ext}. Only text content available.]"

        except Exception as e:
            logger.error("Document processing failed", file_id=file_id, error=str(e))
            raise

    async def _process_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""

        content = []

        # Try pdfplumber first (better for tables)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        content.append(f"--- Page {page_num + 1} ---\n{text}")
        except Exception as e:
            logger.warning("pdfplumber failed, trying PyPDF2", error=str(e))

            # Fallback to PyPDF2
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    content.append(f"--- Page {page_num + 1} ---\n{text}")

        return "\n\n".join(content)

    async def _process_excel(self, file_path: Path) -> str:
        """Extract data from Excel file"""

        output = []

        # Read all sheets
        excel_file = pd.ExcelFile(file_path)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            output.append(f"--- Sheet: {sheet_name} ---")
            output.append(df.to_markdown(index=False))
            output.append("")

        return "\n".join(output)

    async def _process_csv(self, file_path: Path) -> str:
        """Extract data from CSV file"""

        df = pd.read_csv(file_path)
        return f"--- CSV Data ---\n{df.to_markdown(index=False)}"

    async def _process_text(self, file_path: Path) -> str:
        """Read text file"""

        content = await temp_manager.read_file(str(file_path.name).split(".")[0])

        if content:
            return content.decode("utf-8")

        return ""
