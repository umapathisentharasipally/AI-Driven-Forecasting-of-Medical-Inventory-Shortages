from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.response_handler import success_response
from app.api.v1.routes._route_utils import serialize_doc

router = APIRouter()


@router.get("/stockout-risk/")
async def stockout_risk(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    pipeline = [
        {
            "$group": {
                "_id": {"$toLower": "$risk_level"},
                "count": {"$sum": 1},
            }
        }
    ]

    rows = await db["predictions"].aggregate(pipeline).to_list(None)

    data = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for row in rows:
        risk = row["_id"]
        if risk in data:
            data[risk] = row["count"]

    return success_response(data=data, message="Stockout risk fetched successfully")


@router.get("/inventory-value-trend/")
async def inventory_value_trend(
    period: str = Query(default="7d"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    days_map = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }

    days = days_map.get(period, 7)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "snapshot_date": {"$gte": start_date},
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$snapshot_date",
                    }
                },
                "value": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$current_stock_on_hand", 0]},
                            {"$ifNull": ["$unit_cost", 0]},
                        ]
                    }
                },
                "total_stock": {
                    "$sum": {"$ifNull": ["$current_stock_on_hand", 0]}
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "value": {"$round": ["$value", 2]},
                "total_stock": 1,
            }
        },
    ]

    data = await db["inventory_items"].aggregate(pipeline).to_list(None)

    return success_response(data=data, message="Inventory value trend fetched successfully")


@router.get("/top-risk-items/")
async def top_risk_items(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    pipeline = [
        {"$sort": {"stockout_probability": -1, "prediction_date": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "inventory_items",
                "localField": "item_id",
                "foreignField": "item_id",
                "as": "inventory",
            }
        },
        {
            "$unwind": {
                "path": "$inventory",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$project": {
                "_id": 1,
                "item_id": 1,
                "item_name": "$inventory.item_name",
                "facility_id": 1,
                "risk_level": 1,
                "stockout_probability": 1,
                "days_of_supply_on_hand": 1,
                "current_stock_on_hand": "$inventory.current_stock_on_hand",
                "safety_stock_level": "$inventory.safety_stock_level",
                "prediction_date": 1,
            }
        },
    ]

    data = await db["predictions"].aggregate(pipeline).to_list(limit)

    return success_response(
        data=[serialize_doc(item) for item in data],
        message="Top risk items fetched successfully",
    )


@router.get("/predictions/")
async def analytics_predictions(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    total_predictions = await db["predictions"].count_documents({})
    high_risk_predictions = await db["predictions"].count_documents(
        {"risk_level": {"$regex": "^high$", "$options": "i"}}
    )

    latest_prediction = await db["predictions"].find_one(
        {},
        sort=[("prediction_date", -1)],
    )

    model_metrics = await db["model_metrics"].find_one(
        {},
        sort=[("created_at", -1)],
    )

    data = {
        "total_predictions": total_predictions,
        "high_risk_predictions": high_risk_predictions,
        "latest_run": serialize_doc(latest_prediction.get("prediction_date"))
        if latest_prediction
        else None,
        "model_metrics": serialize_doc(model_metrics) if model_metrics else None,
    }

    return success_response(data=data, message="Prediction analytics fetched successfully")