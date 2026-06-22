const ROLE_PERMISSIONS = {
  super_admin: ["*"],

  admin: [
    "dashboard:view",
    "inventory:view",
    "inventory:create",
    "inventory:update",
    "inventory:delete",
    "categories:view",
    "vendors:view",
    "purchase_orders:view",
    "stock_transfers:view",
    "receipts:view",
    "alerts:view",
    "reports:view",
    "forecasting:view",
    "users:view",
    "roles:view",
    "audit_logs:view",
    "settings:view"
  ],

  supply_manager: [
    "dashboard:view",
    "inventory:view",
    "inventory:create",
    "inventory:update",
    "vendors:view",
    "purchase_orders:view",
    "stock_transfers:view",
    "receipts:view",
    "alerts:view",
    "reports:view"
  ],

  inventory_manager: [
    "dashboard:view",
    "inventory:view",
    "inventory:create",
    "inventory:update",
    "categories:view",
    "stock_transfers:view",
    "receipts:view",
    "alerts:view",
    "reports:view"
  ],

  analyst: [
    "dashboard:view",
    "forecasting:view",
    "reports:view",
    "alerts:view"
  ],

  pharmacist: [
    "dashboard:view",
    "inventory:view",
    "receipts:view",
    "stock_transfers:view",
    "alerts:view"
  ],

  viewer: [
    "dashboard:view",
    "inventory:view",
    "alerts:view",
    "reports:view"
  ]
};

export function getCurrentRole() {
  return localStorage.getItem("role") || "viewer";
}

export function can(permission) {
  const role = getCurrentRole();
  const permissions = ROLE_PERMISSIONS[role] || [];

  return permissions.includes("*") || permissions.includes(permission);
}

export function requirePermission(permission) {
  if (!can(permission)) {
    throw new Error("You do not have permission to access this page.");
  }
}