"""File upload API endpoints"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.attachment import attachment_service
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return file ID"""

    try:
        result = await attachment_service.upload_file(file)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("File upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    """Get a temporary file by ID"""

    from fastapi.responses import FileResponse
    from src.utils.temp_manager import temp_manager

    file_path = temp_manager.get_temp_path(file_id)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
