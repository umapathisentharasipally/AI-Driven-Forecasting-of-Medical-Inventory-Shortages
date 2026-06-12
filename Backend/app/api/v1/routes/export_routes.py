from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.exception_handler import NotFoundException
from app.core.permissions import REPORT_READ
from app.core.response_handler import success_response
from app.core.role_checker import RoleChecker
from app.schemas.export_schema import ExportRequest
from app.services import export_service

router = APIRouter()

EXPORT_DIR = Path("exports")


@router.post("/")
async def export_collection(
    data: ExportRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([REPORT_READ])),
):
    result = await export_service.export_collection(
        db=db,
        export_type=data.export_type,
        filters=data.filters,
        format=data.format,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=result.model_dump(mode="json"),
        message="Export generated successfully",
    )


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: dict = Depends(RoleChecker([REPORT_READ])),
):
    safe_name = Path(filename).name
    file_path = EXPORT_DIR / safe_name

    if safe_name != filename:
        raise NotFoundException("Export file not found")

    if not file_path.exists() or not file_path.is_file():
        raise NotFoundException("Export file not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )