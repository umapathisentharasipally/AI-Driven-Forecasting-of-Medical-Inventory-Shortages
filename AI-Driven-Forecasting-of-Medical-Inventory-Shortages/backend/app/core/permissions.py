INVENTORY_READ = "inventory:read"
INVENTORY_WRITE = "inventory:write"
INVENTORY_DELETE = "inventory:delete"

VENDOR_READ = "vendor:read"
VENDOR_WRITE = "vendor:write"

PREDICTION_READ = "prediction:read"
PREDICTION_RUN = "prediction:run"

ALERT_READ = "alert:read"
ALERT_WRITE = "alert:write"

REPORT_READ = "report:read"
REPORT_GENERATE = "report:generate"

USER_READ = "user:read"
USER_WRITE = "user:write"
USER_DELETE = "user:delete"

AUDIT_READ = "audit:read"

ADMIN_ALL = "admin:all"

ROLE_PERMISSIONS = {
    "admin": [ADMIN_ALL],
    "supply_manager": [
        INVENTORY_READ,
        INVENTORY_WRITE,
        INVENTORY_DELETE,
        VENDOR_READ,
        VENDOR_WRITE,
        ALERT_READ,
        ALERT_WRITE,
        REPORT_READ,
        REPORT_GENERATE,
        PREDICTION_READ,
    ],
    "analyst": [
        PREDICTION_READ,
        PREDICTION_RUN,
        REPORT_READ,
        INVENTORY_READ,
        VENDOR_READ,
    ],
    "viewer": [
        INVENTORY_READ,
        VENDOR_READ,
        PREDICTION_READ,
        ALERT_READ,
        REPORT_READ,
    ],
}