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
    analyticas_routes,
    audit_log_routes,
    auth_routes,
    category_routes,
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
    facility_routes,
    department_routes,
    purchase_order_routes,
    settings_routes,
    receipt_routes,
    transfer_routes,
    expiry_routes,
    prescription_routes,
)

from app.realtime.websocket_routes import router as websocket_router

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
api_router.include_router(_get_router(inventory_routes, "inventory_routes.py"), prefix="/products", tags=["Products Compatibility"]) 
api_router.include_router(_get_router(category_routes, "category_routes.py"), prefix="/categories", tags=["Categories"]) 

api_router.include_router(_get_router(vendor_routes, "vendor_routes.py"), prefix="/vendors", tags=["Vendors"]) 

# Facilities & Departments
api_router.include_router(_get_router(facility_routes, "facility_routes.py"), prefix="/facilities", tags=["Facilities"])
api_router.include_router(_get_router(department_routes, "department_routes.py"), prefix="/departments", tags=["Departments"])

# Procurement & Stock Operations
api_router.include_router(_get_router(purchase_order_routes, "purchase_order_routes.py"), prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(_get_router(settings_routes, "settings_routes.py"), prefix="/settings", tags=["Settings"])
api_router.include_router(_get_router(receipt_routes, "receipt_routes.py"), prefix="/receipts", tags=["Stock Receipts"])
api_router.include_router(_get_router(transfer_routes, "transfer_routes.py"), prefix="/transfers", tags=["Stock Transfers"])
api_router.include_router(_get_router(expiry_routes, "expiry_routes.py"), prefix="/expiry", tags=["Expiry Management"])
api_router.include_router(_get_router(prescription_routes, "prescription_routes.py"), prefix="/prescriptions", tags=["Prescriptions"])


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

api_router.include_router(_get_router(analyticas_routes, "analyticas_routes.py"), prefix="/analytics", tags=["Analytics"])  
api_router.include_router(websocket_router, tags=["WebSocket"])