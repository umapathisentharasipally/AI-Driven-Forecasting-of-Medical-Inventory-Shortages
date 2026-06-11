from fastapi import APIRouter

api_router = APIRouter()


def empty_router() -> APIRouter:
    return APIRouter()


auth_router = empty_router()
user_router = empty_router()
role_router = empty_router()
inventory_router = empty_router()
vendor_router = empty_router()
prediction_router = empty_router()
anomaly_router = empty_router()
trend_router = empty_router()
alert_router = empty_router()
notification_router = empty_router()
report_router = empty_router()
upload_router = empty_router()
export_router = empty_router()
dashboard_router = empty_router()
audit_log_router = empty_router()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(role_router, prefix="/roles", tags=["Roles"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(vendor_router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(prediction_router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(anomaly_router, prefix="/anomalies", tags=["Anomalies"])
api_router.include_router(trend_router, prefix="/trends", tags=["Trends"])
api_router.include_router(alert_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(report_router, prefix="/reports", tags=["Reports"])
api_router.include_router(upload_router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(export_router, prefix="/exports", tags=["Exports"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(audit_log_router, prefix="/audit-logs", tags=["Audit Logs"])