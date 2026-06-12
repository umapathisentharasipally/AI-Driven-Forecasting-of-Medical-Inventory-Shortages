import asyncio
from datetime import datetime, timezone
from typing import List, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import NotFoundException
from app.core.permissions import ADMIN_ALL, ALERT_READ, ROLE_PERMISSIONS
from app.repositories import alert_repository, notification_repository
from app.schemas.alert_schema import (
    AlertAssignRequest,
    AlertDashboardCounts,
    AlertFilter,
    AlertResponse,
    AlertStatusUpdate,
)
from app.utils.date_utils import parse_date, utc_now
from app.utils.logger import get_logger
from app.utils.validation_utils import validate_pagination, to_object_id

logger = get_logger(__name__)

SEVERITY_MAPPING = {
    "Critical": "Critical",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
}


def _anomaly_severity(score: float) -> str:
    if score > 0.8:
        return "High"
    if score > 0.5:
        return "Medium"
    return "Low"


def _below_safety_severity(current: float, safety: float) -> str:
    if current < 0.5 * safety:
        return "Critical"
    return "High"


def _expiry_severity(days: int) -> str:
    if days < 7:
        return "Critical"
    if days < 30:
        return "High"
    return "Medium"


def to_alert_response(alert: dict) -> AlertResponse:
    return AlertResponse(
        id=str(alert["_id"]),
        item_id=alert["item_id"],
        facility_id=alert["facility_id"],
        inventory_doc_id=alert["inventory_doc_id"],
        prediction_id=alert.get("prediction_id"),
        anomaly_id=alert.get("anomaly_id"),
        alert_type=alert["alert_type"],
        severity=alert["severity"],
        message=alert["message"],
        status=alert["status"],
        assigned_to=alert.get("assigned_to"),
        snoozed_until=alert.get("snoozed_until"),
        resolved_at=alert.get("resolved_at"),
        created_at=alert["created_at"],
        updated_at=alert["updated_at"],
    )


async def _create_alert_if_not_duplicate(
    db: AsyncIOMotorDatabase,
    alert_doc: dict,
) -> dict | None:
    duplicate = await alert_repository.find_existing_open(
        db=db,
        item_id=alert_doc["item_id"],
        facility_id=alert_doc["facility_id"],
        alert_type=alert_doc["alert_type"],
    )

    if duplicate:
        return None

    created = await alert_repository.create(db, alert_doc)
    asyncio.create_task(_notify_users(db, created))
    return created


async def create_stockout_alert(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    inventory_doc_id: str,
    prediction_id: str,
    stockout_probability: float,
    risk_level: str,
    item_name: str,
) -> dict | None:
    now = utc_now()
    severity = SEVERITY_MAPPING.get(risk_level, "Medium")

    alert_doc = {
        "item_id": item_id,
        "facility_id": facility_id,
        "inventory_doc_id": inventory_doc_id,
        "prediction_id": prediction_id,
        "anomaly_id": None,
        "alert_type": "stockout_risk",
        "severity": severity,
        "message": f"Item {item_name} at {stockout_probability:.0%} stockout risk",
        "status": "open",
        "assigned_to": None,
        "snoozed_until": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }

    return await _create_alert_if_not_duplicate(db, alert_doc)


async def create_below_safety_alert(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    inventory_doc_id: str,
    current_stock: float,
    safety_level: float,
    item_name: str,
) -> dict | None:
    now = utc_now()
    severity = _below_safety_severity(current_stock, safety_level)

    alert_doc = {
        "item_id": item_id,
        "facility_id": facility_id,
        "inventory_doc_id": inventory_doc_id,
        "prediction_id": None,
        "anomaly_id": None,
        "alert_type": "below_safety",
        "severity": severity,
        "message": (
            f"Item {item_name} is below safety stock "
            f"({current_stock}/{safety_level})"
        ),
        "status": "open",
        "assigned_to": None,
        "snoozed_until": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }

    return await _create_alert_if_not_duplicate(db, alert_doc)


async def create_expiry_alert(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    inventory_doc_id: str,
    expiry_date: datetime,
    item_name: str,
) -> dict | None:
    now = utc_now()

    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)

    days = max((expiry_date - now).days, 0)
    severity = _expiry_severity(days)

    alert_doc = {
        "item_id": item_id,
        "facility_id": facility_id,
        "inventory_doc_id": inventory_doc_id,
        "prediction_id": None,
        "anomaly_id": None,
        "alert_type": "expiry",
        "severity": severity,
        "message": f"Item {item_name} expires in {days} days",
        "status": "open",
        "assigned_to": None,
        "snoozed_until": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }

    return await _create_alert_if_not_duplicate(db, alert_doc)


async def create_anomaly_alert(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
    inventory_doc_id: str,
    anomaly_id: str,
    anomaly_score: float,
    item_name: str,
) -> dict | None:
    now = utc_now()
    severity = _anomaly_severity(anomaly_score)

    alert_doc = {
        "item_id": item_id,
        "facility_id": facility_id,
        "inventory_doc_id": inventory_doc_id,
        "prediction_id": None,
        "anomaly_id": anomaly_id,
        "alert_type": "anomaly",
        "severity": severity,
        "message": f"Item {item_name} has anomaly score {anomaly_score:.2f}",
        "status": "open",
        "assigned_to": None,
        "snoozed_until": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }

    return await _create_alert_if_not_duplicate(db, alert_doc)


async def get_alerts(
    db: AsyncIOMotorDatabase,
    filters: AlertFilter,
) -> Tuple[List[AlertResponse], int]:
    page, limit = validate_pagination(filters.page, filters.limit)

    alerts, total = await alert_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters=filters.model_dump(exclude_none=True),
    )

    return [to_alert_response(alert) for alert in alerts], total


async def get_alert(db: AsyncIOMotorDatabase, id: str) -> AlertResponse:
    alert = await alert_repository.get_by_id(db, id)
    if not alert:
        raise NotFoundException("Alert not found")
    return to_alert_response(alert)


async def update_status(
    db: AsyncIOMotorDatabase,
    id: str,
    data: AlertStatusUpdate,
    current_user_id: str,
) -> AlertResponse:
    existing = await alert_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Alert not found")

    extra_fields = {
        "resolved_at": None,
        "snoozed_until": None,
    }

    if data.status == "resolved":
        extra_fields["resolved_at"] = data.resolved_at or utc_now()

    if data.status == "snoozed":
        extra_fields["snoozed_until"] = data.snoozed_until

    updated = await alert_repository.update_status(
        db=db,
        id=id,
        status=data.status,
        extra_fields=extra_fields,
    )

    if not updated:
        raise NotFoundException("Alert not found")

    return to_alert_response(updated)

async def assign_alert(
    db: AsyncIOMotorDatabase,
    id: str,
    data: AlertAssignRequest,
) -> AlertResponse:
    existing = await alert_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Alert not found")

    user = await db["users"].find_one({"_id": to_object_id(data.user_id)})
    if not user:
        raise NotFoundException("Assigned user not found")

    updated = await alert_repository.assign(
        db=db,
        id=id,
        user_id=data.user_id,
    )

    if not updated:
        raise NotFoundException("Alert not found")

    return to_alert_response(updated)

async def get_dashboard_counts(db: AsyncIOMotorDatabase) -> AlertDashboardCounts:
    counts = await alert_repository.get_dashboard_counts(db)
    return AlertDashboardCounts(**counts)


async def _notify_users(db: AsyncIOMotorDatabase, alert: dict) -> None:
    try:
        allowed_roles = [
            role_name
            for role_name, permissions in ROLE_PERMISSIONS.items()
            if ALERT_READ in permissions or ADMIN_ALL in permissions
        ]

        users = await db["users"].find(
            {
                "is_active": True,
                "role_name": {"$in": allowed_roles},
            }
        ).to_list(length=None)

        now = utc_now()

        notifications = [
            {
                "user_id": str(user["_id"]),
                "alert_id": str(alert["_id"]),
                "channel": "in_app",
                "title": f"{alert['severity']} alert",
                "body": alert["message"],
                "is_read": False,
                "sent_at": None,
                "created_at": now,
            }
            for user in users
        ]

        await notification_repository.bulk_create(db, notifications)

    except Exception as exc:
        logger.error(f"Notification fan-out failed: {exc}")