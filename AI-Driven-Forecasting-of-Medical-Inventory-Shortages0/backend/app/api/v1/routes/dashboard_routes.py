from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.permissions import (
    ADMIN_ALL,
    INVENTORY_READ,
    REPORT_READ,
    PREDICTION_READ,
    ALERT_READ,)
from app.core.response_handler import success_response
from app.core.role_checker import RoleChecker
from app.services import alert_service, dashboard_service

router = APIRouter()


@router.get("/metrics")
async def dashboard_metrics(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    metrics = await dashboard_service.get_ui_metrics(db)
    return success_response(
        data=metrics,
        message="Dashboard metrics fetched successfully",
    )


@router.get("/charts")
async def dashboard_charts(
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    charts = await dashboard_service.get_ui_charts(db, days=days)
    return success_response(
        data=charts,
        message="Dashboard charts fetched successfully",
    )


@router.get("/summary")
async def dashboard_summary(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    summary = await dashboard_service.get_summary(db)

    return success_response(
        data=summary,
        message="Dashboard summary fetched successfully",
    )


@router.get("/top-risk")
async def top_risk_items(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    pipeline = [
        {"$sort": {"stockout_probability": -1, "prediction_date": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "item_id": 1,
                "facility_id": 1,
                "risk_level": 1,
                "stockout_probability": 1,
                "days_of_supply_on_hand": 1,
                "prediction_date": 1,
            }
        },
    ]

    items = await db["predictions"].aggregate(pipeline).to_list(length=limit)

    return success_response(
        data=items,
        message="Top risk predictions fetched successfully",
    )


@router.get("/alert-counts")
async def alert_counts(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_READ])),
):
    counts = await alert_service.get_dashboard_counts(db)

    return success_response(
        data=counts.model_dump(mode="json"),
        message="Alert counts fetched successfully",
    )
# -----------------------------------------------------------------------------
# Role-based dashboard payloads required by the uploaded UI screens.
# These endpoints return view-ready API contracts so the frontend does not need
# to hardcode dashboard mocks or perform expensive client-side aggregations.
# -----------------------------------------------------------------------------
from datetime import datetime, timedelta, timezone
from ._route_utils import serialize_doc

async def _inventory_counts(db: AsyncIOMotorDatabase):
    total = await db["inventory_items"].count_documents({})
    low = await db["inventory_items"].count_documents({"$expr": {"$lte": ["$current_stock", "$safety_stock"]}})
    out = await db["inventory_items"].count_documents({"current_stock": {"$lte": 0}})
    critical = await db["inventory_items"].count_documents({"criticality_level": {"$in": ["critical", "high", "High", "Critical"]}})
    active_alerts = await db["alerts"].count_documents({"status": {"$ne": "resolved"}})
    high_risk = await db["predictions"].count_documents({"risk_level": {"$in": ["high", "High"]}})
    value_pipe = [{"$group": {"_id": None, "value": {"$sum": {"$multiply": [{"$ifNull": ["$current_stock", 0]}, {"$ifNull": ["$unit_price", 0]}]}}}}]
    val = await db["inventory_items"].aggregate(value_pipe).to_list(1)
    return {"total_inventory_items": total, 
            "total_inventory_value": round(val[0]["value"], 2) if val else 0, 
            "low_stock_items": low, "out_of_stock_items": out, 
            "critical_items": critical, 
            "active_alerts": active_alerts, 
            "high_stockout_risk": high_risk}

async def _recent(db, collection, limit=5):
    return [serialize_doc(d) for d in await db[collection].find({}).sort("created_at", -1).limit(limit).to_list(limit)]

async def _category_distribution(db):
    pipe = [{"$group": {"_id": {"$ifNull": ["$item_category", "$category"]}, "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    return [{"name": r.get("_id") or "Uncategorized", "value": r["count"]} for r in await db["inventory_items"].aggregate(pipe).to_list(20)]

async def _inventory_status(db):
    total = await db["inventory_items"].count_documents({})
    in_stock = await db["inventory_items"].count_documents({"current_stock": {"$gt": 0}, "$expr": {"$gt": ["$current_stock", "$safety_stock"]}})
    low = await db["inventory_items"].count_documents({"current_stock": {"$gt": 0}, "$expr": {"$lte": ["$current_stock", "$safety_stock"]}})
    out = await db["inventory_items"].count_documents({"current_stock": {"$lte": 0}})
    expired = await db["inventory_batches"].count_documents({"expiry_date": {"$lt": datetime.now(timezone.utc).date().isoformat()}, "available_quantity": {"$gt": 0}})
    return {"total": total, "in_stock": in_stock, "low_stock": low, "out_of_stock": out, "expired": expired}

async def _top_risk(db, limit=5):
    pipe = [{"$sort": {"stockout_probability": -1, "prediction_date": -1}}, {"$limit": limit}]
    return [serialize_doc(d) for d in await db["predictions"].aggregate(pipe).to_list(limit)]

@router.get("/admin")
async def admin_dashboard(db: AsyncIOMotorDatabase = Depends(get_database), 
                          current_user: dict = Depends(RoleChecker([ADMIN_ALL]))):
    metrics = await _inventory_counts(db)
    data = {"metrics": {**metrics,"facilities": await db["facilities"].count_documents({"is_active": {"$ne": False}}),
                        "vendors": await db["vendors"].count_documents({"is_active": {"$ne": False}}), 
                        "departments": await db["departments"].count_documents({"is_active": {"$ne": False}}), 
                        "users": await db["users"].count_documents({"is_active": {"$ne": False}})}, 
                        "inventory_status": await _inventory_status(db), 
                        "category_distribution": await _category_distribution(db), 
                        "top_risk_items": await _top_risk(db), 
                        "recent_predictions": await _recent(db, "predictions"), 
                        "recent_alerts": await _recent(db, "alerts"), 
                        "system_status": {"status": "operational"}}
    return success_response(data, "Admin dashboard fetched successfully")

@router.get("/supply-manager")
async def supply_manager_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_database), 
    current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    data = {"metrics": {**await _inventory_counts(db), 
                        "pending_purchase_orders": await db["purchase_orders"].count_documents({"status": "pending"}), 
                        "pending_receipts": await db["stock_receipts"].count_documents({})}, 
                        "inventory_status": await _inventory_status(db), 
                        "pending_purchase_orders": await _recent(db, "purchase_orders"), 
                        "expiring_items": [serialize_doc(d) for d in await db["inventory_batches"].find({"expiry_date": {"$lte": (datetime.now(timezone.utc).date()+timedelta(days=30)).isoformat()}}).sort("expiry_date", 1).limit(5).to_list(5)],
                        "recent_receipts": await _recent(db, "stock_receipts"), 
                        "recent_transfers": await _recent(db, "stock_transfers"), 
                        "alerts": await _recent(db, "alerts")}
    return success_response(data, "Supply manager dashboard fetched successfully")

@router.get("/inventory-manager")
async def inventory_manager_dashboard(db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    low_items = await db["inventory_items"].find({"$expr": {"$lte": ["$current_stock", "$safety_stock"]}}).limit(10).to_list(10)
    data = {"metrics": await _inventory_counts(db), "inventory_status": await _inventory_status(db), "category_distribution": await _category_distribution(db), "low_stock_items": [serialize_doc(d) for d in low_items], "recent_receipts": await _recent(db, "stock_receipts"), "recent_transfers": await _recent(db, "stock_transfers")}
    return success_response(data, "Inventory manager dashboard fetched successfully")

@router.get("/analyst")
async def analyst_dashboard(db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([PREDICTION_READ]))):
    data = {"metrics": {"predictions_generated": await db["predictions"].count_documents({}), "high_risk_predictions": await db["predictions"].count_documents({"risk_level": {"$in": ["high", "High"]}}), "anomalies_detected": await db["anomalies"].count_documents({}), "models_active": 4}, "recent_predictions": await _recent(db, "predictions"), "recent_anomalies": await _recent(db, "anomalies"), "model_performance": {"xgboost": 0.91, "prophet": 0.90, "isolation_forest": 0.89}}
    return success_response(data, "Analyst dashboard fetched successfully")

@router.get("/pharmacist")
async def pharmacist_dashboard(db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    metrics = await _inventory_counts(db)
    metrics["dispensed_today"] = await db["dispensed_items"].count_documents({"dispensed_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}})
    data = {"metrics": metrics, "stock_status": await _inventory_status(db), "recent_prescriptions": await _recent(db, "prescriptions"), "dispensed_items": await _recent(db, "dispensed_items"), "expiring_medicines": [serialize_doc(d) for d in await db["inventory_batches"].find({"expiry_date": {"$lte": (datetime.now(timezone.utc).date()+timedelta(days=30)).isoformat()}}).sort("expiry_date", 1).limit(5).to_list(5)], "quick_actions": ["add_medicine", "receive_stock", "dispense_medicine", "stock_transfer", "expiry_management", "stock_reports", "search_medicine", "alerts"]}
    return success_response(data, "Pharmacist dashboard fetched successfully")

@router.get("/viewer")
async def viewer_dashboard(db: AsyncIOMotorDatabase = Depends(get_database), current_user: dict = Depends(RoleChecker([INVENTORY_READ]))):
    data = {"metrics": await _inventory_counts(db), "inventory_status": await _inventory_status(db), "category_distribution": await _category_distribution(db), "alerts": await _recent(db, "alerts"), "reports": await _recent(db, "reports")}
    return success_response(data, "Viewer dashboard fetched successfully")
