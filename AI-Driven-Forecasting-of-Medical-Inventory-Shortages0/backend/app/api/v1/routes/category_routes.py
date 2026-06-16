from typing import Optional
import re

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import INVENTORY_READ
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker

router = APIRouter()


@router.get("/")
async def list_categories(
    search: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    match_stage = {"is_active": True}
    if search:
        match_stage["category"] = {"$regex": re.escape(search.strip()), "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$category",
                "items_count": {"$sum": 1},
                "low_stock_count": {
                    "$sum": {
                        "$cond": [
                            {"$lt": ["$current_stock_on_hand", "$safety_stock_level"]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$facet": {
                "items": [
                    {"$skip": offset},
                    {"$limit": limit},
                    {
                        "$project": {
                            "_id": 0,
                            "name": "$_id",
                            "items_count": 1,
                            "low_stock_count": 1,
                        }
                    },
                ],
                "total": [{"$count": "count"}],
            }
        },
    ]
    result = await db["inventory_items"].aggregate(pipeline).to_list(1)
    data = result[0] if result else {"items": [], "total": []}
    total_data = data.get("total", [])
    total = total_data[0]["count"] if total_data else 0
    page = (offset // limit) + 1

    return paginated_response(
        data=data.get("items", []),
        total=total,
        page=page,
        limit=limit,
        message="Categories fetched successfully",
    )


@router.get("/{category_name}")
async def get_category_summary(
    category_name: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    pipeline = [
        {"$match": {"category": category_name, "is_active": True}},
        {
            "$group": {
                "_id": "$category",
                "items_count": {"$sum": 1},
                "low_stock_count": {
                    "$sum": {
                        "$cond": [
                            {"$lt": ["$current_stock_on_hand", "$safety_stock_level"]},
                            1,
                            0,
                        ]
                    }
                },
                "critical_count": {"$sum": {"$cond": ["$is_critical", 1, 0]}},
            }
        },
        {"$project": {"_id": 0, "name": "$_id", "items_count": 1, "low_stock_count": 1, "critical_count": 1}},
    ]
    result = await db["inventory_items"].aggregate(pipeline).to_list(1)
    return success_response(
        data=result[0] if result else {"name": category_name, "items_count": 0, "low_stock_count": 0, "critical_count": 0},
        message="Category summary fetched successfully",
    )
