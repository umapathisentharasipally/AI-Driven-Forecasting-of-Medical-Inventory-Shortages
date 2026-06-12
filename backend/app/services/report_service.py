import asyncio
import csv
import json
from datetime import timedelta
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import NotFoundException, ValidationException
from app.repositories import report_repository
from app.schemas.report_schema import ReportResponse
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger
from app.utils.validation_utils import validate_pagination

logger = get_logger(__name__)

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def _serialize(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__str__"):
        return str(value)
    return value


def _report_response(report: dict) -> ReportResponse:
    return ReportResponse(
        id=str(report["_id"]),
        report_type=report["report_type"],
        generated_by=report.get("generated_by"),
        period_start=report["period_start"],
        period_end=report["period_end"],
        status=report["status"],
        file_path=report.get("file_path"),
        summary=report.get("summary"),
        created_at=report["created_at"],
    )


async def _create_report_record(
    db: AsyncIOMotorDatabase,
    report_type: str,
    period_start,
    period_end,
    user_id: str | None,
) -> dict:
    return await report_repository.create(
        db,
        {
            "report_type": report_type,
            "generated_by": user_id,
            "period_start": period_start,
            "period_end": period_end,
            "status": "generating",
            "file_path": None,
            "summary": None,
            "created_at": utc_now(),
        },
    )


async def generate_daily_summary(
    db: AsyncIOMotorDatabase,
    period_start,
    period_end,
    user_id: str | None,
) -> ReportResponse:
    report = await _create_report_record(
        db, "daily_summary", period_start, period_end, user_id
    )

    asyncio.create_task(
        _generate_daily_summary_task(db, str(report["_id"]), period_start, period_end)
    )

    return _report_response(report)


async def _generate_daily_summary_task(
    db: AsyncIOMotorDatabase,
    report_id: str,
    period_start,
    period_end,
) -> None:
    try:
        now = utc_now()
        expiring_until = now + timedelta(days=30)

        pipeline = [
            {
                "$facet": {
                    "inventory_stats": [
                        {"$match": {"is_active": True}},
                        {
                            "$group": {
                                "_id": None,
                                "total_active": {"$sum": 1},
                                "critical_count": {
                                    "$sum": {"$cond": ["$is_critical", 1, 0]}
                                },
                                "below_safety_count": {
                                    "$sum": {
                                        "$cond": [
                                            {
                                                "$lt": [
                                                    "$current_stock_on_hand",
                                                    "$safety_stock_level",
                                                ]
                                            },
                                            1,
                                            0,
                                        ]
                                    }
                                },
                                "expiring_30d_count": {
                                    "$sum": {
                                        "$cond": [
                                            {
                                                "$and": [
                                                    {"$ne": ["$expiry_date", None]},
                                                    {"$lte": ["$expiry_date", expiring_until]},
                                                    {"$gte": ["$expiry_date", now]},
                                                ]
                                            },
                                            1,
                                            0,
                                        ]
                                    }
                                },
                            }
                        },
                        {"$project": {"_id": 0}},
                    ],
                    "alert_stats": [
                        {
                            "$lookup": {
                                "from": "alerts",
                                "pipeline": [
                                    {
                                        "$facet": {
                                            "open_critical": [
                                                {
                                                    "$match": {
                                                        "status": "open",
                                                        "severity": "Critical",
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                            "open_high": [
                                                {
                                                    "$match": {
                                                        "status": "open",
                                                        "severity": "High",
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                            "open_total": [
                                                {"$match": {"status": "open"}},
                                                {"$count": "count"},
                                            ],
                                            "resolved_in_period": [
                                                {
                                                    "$match": {
                                                        "status": "resolved",
                                                        "resolved_at": {
                                                            "$gte": period_start,
                                                            "$lte": period_end,
                                                        },
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                        }
                                    }
                                ],
                                "as": "alert_stats",
                            }
                        },
                        {"$limit": 1},
                        {
                            "$project": {
                                "_id": 0,
                                "alert_stats": {
                                    "$ifNull": [
                                        {"$arrayElemAt": ["$alert_stats", 0]},
                                        {},
                                    ]
                                },
                            }
                        },
                    ],
                    "prediction_stats": [
                        {
                            "$lookup": {
                                "from": "predictions",
                                "pipeline": [
                                    {
                                        "$facet": {
                                            "high_risk_count": [
                                                {
                                                    "$match": {
                                                        "prediction_date": {
                                                            "$gte": period_start,
                                                            "$lte": period_end,
                                                        },
                                                        "risk_level": {
                                                            "$in": ["High", "Critical"]
                                                        },
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                            "predictions_in_period": [
                                                {
                                                    "$match": {
                                                        "prediction_date": {
                                                            "$gte": period_start,
                                                            "$lte": period_end,
                                                        }
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                        }
                                    }
                                ],
                                "as": "prediction_stats",
                            }
                        },
                        {"$limit": 1},
                        {
                            "$project": {
                                "_id": 0,
                                "prediction_stats": {
                                    "$ifNull": [
                                        {"$arrayElemAt": ["$prediction_stats", 0]},
                                        {},
                                    ]
                                },
                            }
                        },
                    ],
                    "anomaly_stats": [
                        {
                            "$lookup": {
                                "from": "anomalies",
                                "pipeline": [
                                    {
                                        "$facet": {
                                            "detected_in_period": [
                                                {
                                                    "$match": {
                                                        "detected_at": {
                                                            "$gte": period_start,
                                                            "$lte": period_end,
                                                        }
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                            "unacknowledged_count": [
                                                {
                                                    "$match": {
                                                        "is_acknowledged": False
                                                    }
                                                },
                                                {"$count": "count"},
                                            ],
                                        }
                                    }
                                ],
                                "as": "anomaly_stats",
                            }
                        },
                        {"$limit": 1},
                        {
                            "$project": {
                                "_id": 0,
                                "anomaly_stats": {
                                    "$ifNull": [
                                        {"$arrayElemAt": ["$anomaly_stats", 0]},
                                        {},
                                    ]
                                },
                            }
                        },
                    ],
                    "top_10_risk": [
                        {"$match": {"is_active": True}},
                        {
                            "$lookup": {
                                "from": "predictions",
                                "let": {
                                    "item_id": "$item_id",
                                    "facility_id": "$facility_id",
                                },
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {
                                                "$and": [
                                                    {"$eq": ["$item_id", "$$item_id"]},
                                                    {
                                                        "$eq": [
                                                            "$facility_id",
                                                            "$$facility_id",
                                                        ]
                                                    },
                                                ]
                                            }
                                        }
                                    },
                                    {"$sort": {"stockout_probability": -1}},
                                    {"$limit": 1},
                                ],
                                "as": "prediction",
                            }
                        },
                        {"$unwind": "$prediction"},
                        {"$sort": {"prediction.stockout_probability": -1}},
                        {"$limit": 10},
                        {
                            "$project": {
                                "_id": 0,
                                "item_id": 1,
                                "item_name": 1,
                                "facility_id": 1,
                                "risk_level": "$prediction.risk_level",
                                "stockout_probability": "$prediction.stockout_probability",
                                "days_of_supply_on_hand": 1,
                            }
                        },
                    ],
                }
            }
        ]

        result = await db["inventory_items"].aggregate(pipeline).to_list(1)
        raw = result[0] if result else {}

        summary = {
            "inventory_stats": raw.get("inventory_stats", []),
            "alert_stats": (
                raw.get("alert_stats", [{}])[0].get("alert_stats", {})
                if raw.get("alert_stats")
                else {}
            ),
            "prediction_stats": (
                raw.get("prediction_stats", [{}])[0].get("prediction_stats", {})
                if raw.get("prediction_stats")
                else {}
            ),
            "anomaly_stats": (
                raw.get("anomaly_stats", [{}])[0].get("anomaly_stats", {})
                if raw.get("anomaly_stats")
                else {}
            ),
            "top_10_risk": raw.get("top_10_risk", []),
        }

        filename = f"daily_summary_{period_start.date()}_{uuid4().hex[:8]}.json"
        file_path = REPORT_DIR / filename

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(summary, file, default=_serialize, indent=2)

        await report_repository.update_status(
            db, report_id, "ready", str(file_path), summary
        )

    except Exception as exc:
        logger.error(f"Daily summary report failed: {exc}")
        await report_repository.update_status(db, report_id, "failed", None, None)


async def generate_stockout_risk_report(
    db: AsyncIOMotorDatabase,
    period_start,
    period_end,
    user_id: str | None,
) -> ReportResponse:
    report = await _create_report_record(
        db, "stockout_risk", period_start, period_end, user_id
    )
    asyncio.create_task(
        _generate_stockout_risk_report_task(
            db, str(report["_id"]), period_start, period_end
        )
    )
    return _report_response(report)


async def _generate_stockout_risk_report_task(
    db: AsyncIOMotorDatabase,
    report_id: str,
    period_start,
    period_end,
) -> None:
    try:
        pipeline = [
            {
                "$match": {
                    "prediction_date": {"$gte": period_start, "$lte": period_end},
                    "risk_level": {"$in": ["High", "Critical"]},
                }
            },
            {
                "$lookup": {
                    "from": "inventory_items",
                    "let": {"item_id": "$item_id", "facility_id": "$facility_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$item_id", "$$item_id"]},
                                        {"$eq": ["$facility_id", "$$facility_id"]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "inventory",
                }
            },
            {"$unwind": {"path": "$inventory", "preserveNullAndEmptyArrays": True}},
        ]

        rows = await db["predictions"].aggregate(pipeline).to_list(length=None)

        filename = f"stockout_risk_{period_start.date()}.csv"
        file_path = REPORT_DIR / filename

        columns = [
            "item_id",
            "item_name",
            "facility_id",
            "risk_level",
            "stockout_probability",
            "days_of_supply_on_hand",
            "vendor_reliability_score",
            "prediction_date",
        ]

        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for row in rows:
                inventory = row.get("inventory", {})
                writer.writerow(
                    {
                        "item_id": row.get("item_id"),
                        "item_name": inventory.get("item_name"),
                        "facility_id": row.get("facility_id"),
                        "risk_level": row.get("risk_level"),
                        "stockout_probability": row.get("stockout_probability"),
                        "days_of_supply_on_hand": row.get("days_of_supply_on_hand"),
                        "vendor_reliability_score": inventory.get(
                            "vendor_reliability_score"
                        ),
                        "prediction_date": _serialize(row.get("prediction_date")),
                    }
                )

        summary = {"rows": len(rows)}

        await report_repository.update_status(
            db, report_id, "ready", str(file_path), summary
        )

    except Exception as exc:
        logger.error(f"Stockout risk report failed: {exc}")
        await report_repository.update_status(db, report_id, "failed", None, None)


async def generate_vendor_performance_report(
    db: AsyncIOMotorDatabase,
    period_start,
    period_end,
    user_id: str | None,
) -> ReportResponse:
    report = await _create_report_record(
        db, "vendor_performance", period_start, period_end, user_id
    )

    asyncio.create_task(
        _generate_vendor_performance_report_task(
            db, str(report["_id"]), period_start, period_end
        )
    )

    return _report_response(report)


async def _generate_vendor_performance_report_task(
    db: AsyncIOMotorDatabase,
    report_id: str,
    period_start,
    period_end,
) -> None:
    try:
        pipeline = [
            {"$match": {"created_at": {"$gte": period_start, "$lte": period_end}}},
            {
                "$group": {
                    "_id": "$facility_id",
                    "alert_count": {"$sum": 1},
                    "critical_count": {
                        "$sum": {"$cond": [{"$eq": ["$severity", "Critical"]}, 1, 0]}
                    },
                    "high_count": {
                        "$sum": {"$cond": [{"$eq": ["$severity", "High"]}, 1, 0]}
                    },
                }
            },
        ]

        rows = await db["alerts"].aggregate(pipeline).to_list(length=None)

        filename = f"vendor_performance_{period_start.date()}.csv"
        file_path = REPORT_DIR / filename

        columns = ["facility_id", "alert_count", "critical_count", "high_count"]

        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "facility_id": row["_id"],
                        "alert_count": row["alert_count"],
                        "critical_count": row["critical_count"],
                        "high_count": row["high_count"],
                    }
                )

        await report_repository.update_status(
            db, report_id, "ready", str(file_path), {"rows": len(rows)}
        )

    except Exception as exc:
        logger.error(f"Vendor performance report failed: {exc}")
        await report_repository.update_status(db, report_id, "failed", None, None)


async def get_reports(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    report_type: str | None,
) -> Tuple[List[ReportResponse], int]:
    page, limit = validate_pagination(page, limit)

    reports, total = await report_repository.get_all(db, page, limit, report_type)

    return [_report_response(report) for report in reports], total


async def get_report(
    db: AsyncIOMotorDatabase,
    id: str,
) -> ReportResponse:
    report = await report_repository.get_by_id(db, id)
    if not report:
        raise NotFoundException("Report not found")
    return _report_response(report)


async def get_report_file(
    db: AsyncIOMotorDatabase,
    report_id: str,
) -> str:
    report = await report_repository.get_by_id(db, report_id)
    if not report:
        raise NotFoundException("Report not found")

    if report["status"] != "ready" or not report.get("file_path"):
        raise ValidationException("Report is not ready for download")

    file_path = Path(report["file_path"])
    if not file_path.exists():
        raise NotFoundException("Report file not found")

    return str(file_path)

async def generate_anomaly_summary_report(
    db: AsyncIOMotorDatabase,
    period_start,
    period_end,
    user_id: str | None,
) -> ReportResponse:
    report = await _create_report_record(
        db, "anomaly_summary", period_start, period_end, user_id
    )

    asyncio.create_task(
        _generate_anomaly_summary_report_task(
            db,
            str(report["_id"]),
            period_start,
            period_end,
        )
    )

    return _report_response(report)


async def _generate_anomaly_summary_report_task(
    db: AsyncIOMotorDatabase,
    report_id: str,
    period_start,
    period_end,
) -> None:
    try:
        rows = await db["anomalies"].find(
            {
                "detected_at": {
                    "$gte": period_start,
                    "$lte": period_end,
                }
            }
        ).sort("detected_at", -1).to_list(length=None)

        filename = f"anomaly_summary_{period_start.date()}_{uuid4().hex[:8]}.csv"
        file_path = REPORT_DIR / filename

        columns = [
            "item_id",
            "facility_id",
            "inventory_doc_id",
            "anomaly_score",
            "is_anomaly",
            "is_acknowledged",
            "detected_at",
        ]

        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for row in rows:
                writer.writerow(
                    {
                        "item_id": row.get("item_id"),
                        "facility_id": row.get("facility_id"),
                        "inventory_doc_id": row.get("inventory_doc_id"),
                        "anomaly_score": row.get("anomaly_score"),
                        "is_anomaly": row.get("is_anomaly"),
                        "is_acknowledged": row.get("is_acknowledged"),
                        "detected_at": _serialize(row.get("detected_at")),
                    }
                )

        await report_repository.update_status(
            db,
            report_id,
            "ready",
            str(file_path),
            {"rows": len(rows)},
        )

    except Exception as exc:
        logger.error(f"Anomaly summary report failed: {exc}")
        await report_repository.update_status(db, report_id, "failed", None, None)