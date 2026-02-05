"""Attachment handling service"""

import uuid
from typing import List
from fastapi import UploadFile, HTTPException
from src.utils.temp_manager import temp_manager
from src.config import settings
import structlog

logger = structlog.get_logger(__name__)


class AttachmentService:
    """Service for handling file uploads and attachments"""

    async def upload_file(self, file: UploadFile) -> dict:
        """Upload a file to temp directory"""

        # Validate file size
        content = await file.read()

        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_upload_size} bytes"
            )

        # Validate file type
        if file.content_type not in settings.allowed_mime_types:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}"
            )

        # Generate file ID and save
        file_id = temp_manager.generate_file_id(file.filename)
        await temp_manager.save_file(file_id, content)

        logger.info(
            "File uploaded",
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            mime_type=file.content_type
        )

        return {
            "file_id": file_id,
            "filename": file.filename,
            "mime_type": file.content_type,
            "size": len(content),
            "temp_path": str(temp_manager.get_temp_path(file_id))
        }

    async def cleanup_files(self, file_ids: List[str]):
        """Clean up temporary files after processing"""

        for file_id in file_ids:
            try:
                await temp_manager.delete_file(file_id)
            except Exception as e:
                logger.error("Failed to delete temp file", file_id=file_id, error=str(e))


# Global attachment service instance
attachment_service = AttachmentService()
