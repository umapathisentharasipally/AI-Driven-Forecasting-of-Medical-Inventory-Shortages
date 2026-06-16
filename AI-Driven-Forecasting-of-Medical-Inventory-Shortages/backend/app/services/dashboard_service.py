from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.date_utils import utc_now


async def get_summary(db: AsyncIOMotorDatabase) -> dict:
    now = utc_now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    expiring_until = now + timedelta(days=30)

    pipeline = [
        {
            "$facet": {
                "inventory_stats": [
                    {"$match": {"is_active": True}},
                    {
                        "$group": {
                            "_id": None,
                            "active_count": {"$sum": 1},
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
                                                {"$gte": ["$expiry_date", now]},
                                                {"$lte": ["$expiry_date", expiring_until]},
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "active_count": 1,
                            "critical_count": 1,
                            "below_safety_count": 1,
                            "expiring_30d_count": 1,
                        }
                    },
                ],
                "alert_stats": [
                    {
                        "$lookup": {
                            "from": "alerts",
                            "pipeline": [
                                {
                                    "$facet": {
                                        "open_by_severity": [
                                            {"$match": {"status": "open"}},
                                            {
                                                "$group": {
                                                    "_id": "$severity",
                                                    "count": {"$sum": 1},
                                                }
                                            },
                                        ],
                                        "resolved_today": [
                                            {
                                                "$match": {
                                                    "status": "resolved",
                                                    "resolved_at": {"$gte": start_today},
                                                }
                                            },
                                            {"$count": "count"},
                                        ],
                                        "snoozed": [
                                            {"$match": {"status": "snoozed"}},
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
                                        "predictions_today": [
                                            {
                                                "$match": {
                                                    "prediction_date": {
                                                        "$gte": start_today
                                                    }
                                                }
                                            },
                                            {"$count": "count"},
                                        ],
                                        "high_critical_today": [
                                            {
                                                "$match": {
                                                    "prediction_date": {
                                                        "$gte": start_today
                                                    },
                                                    "risk_level": {
                                                        "$in": ["High", "Critical"]
                                                    },
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
                                        "unacknowledged": [
                                            {"$match": {"is_acknowledged": False}},
                                            {"$count": "count"},
                                        ],
                                        "detected_today": [
                                            {
                                                "$match": {
                                                    "detected_at": {"$gte": start_today}
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
                "top_risk_items": [
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
                                {"$sort": {"prediction_date": -1}},
                                {"$limit": 1},
                            ],
                            "as": "latest_prediction",
                        }
                    },
                    {"$unwind": "$latest_prediction"},
                    {"$sort": {"latest_prediction.stockout_probability": -1}},
                    {"$limit": 10},
                    {
                        "$project": {
                            "_id": 0,
                            "item_name": 1,
                            "item_id": 1,
                            "facility_id": 1,
                            "risk_level": "$latest_prediction.risk_level",
                            "stockout_probability": "$latest_prediction.stockout_probability",
                            "days_of_supply_on_hand": 1,
                        }
                    },
                ],
                "recent_alerts": [
                    {
                        "$lookup": {
                            "from": "alerts",
                            "pipeline": [
                                {"$match": {"status": "open"}},
                                {"$sort": {"created_at": -1}},
                                {"$limit": 5},
                                {
                                    "$project": {
                                        "_id": {"$toString": "$_id"},
                                        "item_id": 1,
                                        "facility_id": 1,
                                        "alert_type": 1,
                                        "severity": 1,
                                        "message": 1,
                                        "created_at": 1,
                                    }
                                },
                            ],
                            "as": "recent_alerts",
                        }
                    },
                    {"$limit": 1},
                    {
                        "$project": {
                            "_id": 0,
                            "recent_alerts": 1,
                        }
                    },
                ],
            }
        }
    ]

    result = await db["inventory_items"].aggregate(pipeline).to_list(length=1)
    data = result[0] if result else {}

    return {
        "inventory_stats": data.get("inventory_stats", []),
        "alert_stats": (
            data.get("alert_stats", [{}])[0].get("alert_stats", {})
            if data.get("alert_stats")
            else {}
        ),
        "prediction_stats": (
            data.get("prediction_stats", [{}])[0].get("prediction_stats", {})
            if data.get("prediction_stats")
            else {}
        ),
        "anomaly_stats": (
            data.get("anomaly_stats", [{}])[0].get("anomaly_stats", {})
            if data.get("anomaly_stats")
            else {}
        ),
        "top_risk_items": data.get("top_risk_items", []),
        "recent_alerts": (
            data.get("recent_alerts", [{}])[0].get("recent_alerts", [])
            if data.get("recent_alerts")
            else []
        ),
    }