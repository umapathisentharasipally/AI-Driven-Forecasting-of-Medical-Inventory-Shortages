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

async def get_ui_metrics(db: AsyncIOMotorDatabase) -> dict:
    """Aggregated metrics for UI dashboard cards.

    The current medical inventory backend does not have dedicated sales/expenses
    collections. This method returns inventory, alert, prediction, and optional
    finance fields. If invoice/restock collections exist later, the optional
    finance values will be populated automatically.
    """
    now = utc_now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    inventory_pipeline = [
        {"$match": {"is_active": True}},
        {
            "$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "low_stock_count": {
                    "$sum": {
                        "$cond": [
                            {"$lt": ["$current_stock_on_hand", "$safety_stock_level"]},
                            1,
                            0,
                        ]
                    }
                },
                "critical_items": {"$sum": {"$cond": ["$is_critical", 1, 0]}},
                "total_stock_on_hand": {"$sum": "$current_stock_on_hand"},
            }
        },
        {"$project": {"_id": 0}},
    ]
    inventory = await db["inventory_items"].aggregate(inventory_pipeline).to_list(1)
    inventory_stats = inventory[0] if inventory else {}

    open_alerts = await db["alerts"].count_documents({"status": "open"})
    unread_notifications = await db["notifications"].count_documents({"is_read": False})
    predictions_today = await db["predictions"].count_documents({"prediction_date": {"$gte": start_today}})
    high_risk_today = await db["predictions"].count_documents(
        {"prediction_date": {"$gte": start_today}, "risk_level": {"$in": ["High", "Critical"]}}
    )

    # Optional finance support for UI templates that show Sales/Expenses/Profit/Purchase.
    # These remain zero until invoice/restock collections are added.
    sales_pipeline = [
        {"$match": {"created_at": {"$gte": start_month}}},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$total_amount", 0]}}}},
    ]
    purchase_pipeline = [
        {"$match": {"created_at": {"$gte": start_month}}},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$total_cost", 0]}}}},
    ]
    monthly_sales_data = await db["invoices"].aggregate(sales_pipeline).to_list(1)
    monthly_purchase_data = await db["restock_orders"].aggregate(purchase_pipeline).to_list(1)
    total_sales = float(monthly_sales_data[0]["total"]) if monthly_sales_data else 0.0
    total_purchase = float(monthly_purchase_data[0]["total"]) if monthly_purchase_data else 0.0

    return {
        "total_items": inventory_stats.get("total_items", 0),
        "low_stock_count": inventory_stats.get("low_stock_count", 0),
        "critical_items": inventory_stats.get("critical_items", 0),
        "total_stock_on_hand": inventory_stats.get("total_stock_on_hand", 0),
        "open_alerts": open_alerts,
        "unread_notifications": unread_notifications,
        "predictions_today": predictions_today,
        "high_risk_today": high_risk_today,
        "total_sales": total_sales,
        "total_purchase": total_purchase,
        "total_expenses": total_purchase,
        "total_profit": total_sales - total_purchase,
        "period": "monthly",
    }


async def get_ui_charts(db: AsyncIOMotorDatabase, days: int = 30) -> dict:
    """Chart-ready arrays for frontend libraries such as Chart.js/Recharts."""
    now = utc_now()
    start_date = now - timedelta(days=days - 1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    prediction_pipeline = [
        {"$match": {"prediction_date": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$prediction_date"}},
                "predictions": {"$sum": 1},
                "high_risk": {
                    "$sum": {"$cond": [{"$in": ["$risk_level", ["High", "Critical"]]}, 1, 0]}
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]
    trend_rows = await db["predictions"].aggregate(prediction_pipeline).to_list(days)

    low_stock_pipeline = [
        {"$match": {"is_active": True}},
        {
            "$group": {
                "_id": "$category",
                "total": {"$sum": 1},
                "low_stock": {
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
    ]
    category_rows = await db["inventory_items"].aggregate(low_stock_pipeline).to_list(None)

    dates = [row["_id"] for row in trend_rows]
    return {
        "prediction_trend": {
            "labels": dates,
            "predictions": [row.get("predictions", 0) for row in trend_rows],
            "high_risk": [row.get("high_risk", 0) for row in trend_rows],
        },
        "category_stock_status": {
            "labels": [row.get("_id", "Unknown") for row in category_rows],
            "total": [row.get("total", 0) for row in category_rows],
            "low_stock": [row.get("low_stock", 0) for row in category_rows],
        },
    }
