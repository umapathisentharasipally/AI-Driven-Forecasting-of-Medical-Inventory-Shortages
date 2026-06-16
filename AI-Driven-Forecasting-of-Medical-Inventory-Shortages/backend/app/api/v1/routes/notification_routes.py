from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.response_handler import paginated_response, success_response
from app.schemas.notification_schema import MarkReadRequest
from app.services import notification_service

router = APIRouter()


@router.get("/")
async def get_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    notifications, total = await notification_service.get_notifications(
        db=db,
        user_id=str(current_user["_id"]),
        page=page,
        limit=limit,
    )

    return paginated_response(
        data=[item.model_dump(mode="json") for item in notifications],
        total=total,
        page=page,
        limit=limit,
        message="Notifications fetched successfully",
    )


@router.get("/unread-count")
async def unread_count(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    count = await notification_service.get_unread_count(
        db=db,
        user_id=str(current_user["_id"]),
    )

    return success_response(
        data={"unread_count": count},
        message="Unread notification count fetched successfully",
    )


@router.patch("/mark-read")
async def mark_read(
    data: MarkReadRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    modified = await notification_service.mark_read(
        db=db,
        user_id=str(current_user["_id"]),
        ids=data.notification_ids,
    )

    return success_response(
        data={"modified_count": modified},
        message="Notifications marked as read successfully",
    )


@router.patch("/mark-all-read")
async def mark_all_read(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    modified = await notification_service.mark_all_read(
        db=db,
        user_id=str(current_user["_id"]),
    )

    return success_response(
        data={"modified_count": modified},
        message="All notifications marked as read successfully",
    )