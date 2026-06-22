const LABELS = {
  dashboard: "Dashboard",
  inventory: "Inventory Items",
  categories: "Categories",
  vendors: "Vendors",
  "purchase-orders": "Purchase Orders",
  "stock-receipts": "Receive Items",
  "stock-transfers": "Stock Transfers",
  alerts: "Alerts",
  forecasting: "Forecast & Trends",
  reports: "Reports",
  users: "Users",
  roles: "Roles & Permissions",
  "audit-logs": "Audit Logs",
  settings: "Settings"
};

export function setBreadcrumb(routeName) {
  const target = document.getElementById("breadcrumbText");

  if (!target) return;

  target.textContent = `Dashboard / ${LABELS[routeName] || "Page"}`;
}