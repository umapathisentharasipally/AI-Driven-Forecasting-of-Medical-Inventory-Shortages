from pathlib import Path
import sys

# Ensure the backend package root is on sys.path when this module is executed directly.
BASE_DIR = Path(__file__).resolve().parents[4]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import APIRouter

from .routes import (
    alert_routes,
    anomaly_routes,
    audit_log_routes,
    auth_routes,
    dashboard_routes,
    export_routes,
    inventory_routes,
    notification_routes,
    prediction_routes,
    report_routes,
    role_routes,
    trend_routes,
    upload_routes,
    user_routes,
    vendor_routes,
)

api_router = APIRouter()

import importlib.util

def _get_router(module_obj, module_filename: str):
    if getattr(module_obj, "router", None) is not None:
        return module_obj.router
    # load from file to avoid partial-import / circular-import issues
    path = Path(__file__).resolve().parents[0] / "routes" / module_filename
    spec = importlib.util.spec_from_file_location(f"app.api.v1.routes.{module_filename[:-3]}", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "router")

# Authentication
api_router.include_router(_get_router(auth_routes, "auth_routes.py"), prefix="/auth", tags=["Auth"]) 

# User & Role Management
api_router.include_router(_get_router(user_routes, "user_routes.py"), prefix="/users", tags=["Users"]) 

api_router.include_router(_get_router(role_routes, "role_routes.py"), prefix="/roles", tags=["Roles"]) 

# Inventory
api_router.include_router(_get_router(inventory_routes, "inventory_routes.py"), prefix="/inventory", tags=["Inventory"]) 

api_router.include_router(_get_router(vendor_routes, "vendor_routes.py"), prefix="/vendors", tags=["Vendors"]) 

# ML
api_router.include_router(_get_router(prediction_routes, "prediction_routes.py"), prefix="/predictions", tags=["Predictions"]) 

api_router.include_router(_get_router(anomaly_routes, "anomaly_routes.py"), prefix="/anomalies", tags=["Anomalies"]) 

api_router.include_router(_get_router(trend_routes, "trend_routes.py"), prefix="/trends", tags=["Trends"]) 

# Alerts & Notifications
api_router.include_router(_get_router(alert_routes, "alert_routes.py"), prefix="/alerts", tags=["Alerts"]) 


api_router.include_router(_get_router(notification_routes, "notification_routes.py"), prefix="/notifications", tags=["Notifications"]) 

# Reports
api_router.include_router(_get_router(report_routes, "report_routes.py"), prefix="/reports", tags=["Reports"]) 

api_router.include_router(_get_router(upload_routes, "upload_routes.py"), prefix="/uploads", tags=["Uploads"]) 

api_router.include_router(_get_router(export_routes, "export_routes.py"), prefix="/exports", tags=["Exports"]) 

# Dashboard
api_router.include_router(_get_router(dashboard_routes, "dashboard_routes.py"), prefix="/dashboard", tags=["Dashboard"]) 

# Audit Logs
api_router.include_router(_get_router(audit_log_routes, "audit_log_routes.py"), prefix="/audit-logs", tags=["Audit Logs"]) 

