"""Temporary file management utilities"""

import os
import aiofiles
import uuid
from pathlib import Path
from typing import Optional
from src.config import settings
import structlog

logger = structlog.get_logger(__name__)


class TempFileManager:
    """Manager for temporary uploaded files"""

    def __init__(self):
        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)

    def generate_file_id(self, filename: str) -> str:
        """Generate a unique file ID"""
        ext = Path(filename).suffix
        return f"{uuid.uuid4()}{ext}"

    def get_temp_path(self, file_id: str) -> Path:
        """Get the full path for a temp file"""
        return self.temp_dir / file_id

    async def save_file(self, file_id: str, content: bytes) -> Path:
        """Save file content to temp directory"""
        temp_path = self.get_temp_path(file_id)

        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)

        logger.info("File saved to temp", file_id=file_id, path=str(temp_path))
        return temp_path

    async def delete_file(self, file_id: str) -> bool:
        """Delete a temp file"""
        temp_path = self.get_temp_path(file_id)

        if temp_path.exists():
            temp_path.unlink()
            logger.info("Temp file deleted", file_id=file_id)
            return True

        return False

    async def read_file(self, file_id: str) -> Optional[bytes]:
        """Read file content from temp directory"""
        temp_path = self.get_temp_path(file_id)

        if temp_path.exists():
            async with aiofiles.open(temp_path, "rb") as f:
                content = await f.read()
            return content

        return None

    def get_file_url(self, file_id: str) -> str:
        """Get file URL for API access"""
        return f"/api/files/{file_id}"

    async def cleanup_old_files(self, max_age_hours: int = None):
        """Clean up files older than specified hours"""
        if max_age_hours is None:
            max_age_hours = settings.temp_file_cleanup_interval

        import time
        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted_count = 0

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1

        logger.info("Temp files cleaned up", count=deleted_count)
        return deleted_count


# Global temp file manager instance
temp_manager = TempFileManager()
