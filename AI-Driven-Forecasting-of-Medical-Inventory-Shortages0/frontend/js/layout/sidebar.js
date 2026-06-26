import { can } from "../auth/permissions.js";

const MENU_GROUPS = [
  {
    title: "MAIN",
    items: [
      { label: "Dashboard", icon: "🏠", route: "dashboard", permission: "dashboard:view" }
    ]
  },
  {
    title: "INVENTORY MANAGEMENT",
    items: [
      { label: "Inventory Items", icon: "📦", route: "inventory", permission: "inventory:view" },
      { label: "Categories", icon: "▦", route: "categories", permission: "categories:view" },
      { label: "Vendors", icon: "🚚", route: "vendors", permission: "vendors:view" }
    ]
  },
  {
    title: "OPERATIONS",
    items: [
      { label: "Purchase Orders", icon: "📋", route: "purchase-orders", permission: "purchase_orders:view" },
      { label: "Receive Items", icon: "📥", route: "stock-receipts", permission: "receipts:view" },
      { label: "Stock Transfers", icon: "🔁", route: "stock-transfers", permission: "stock_transfers:view" }
    ]
  },
  {
    title: "ANALYTICS",
    items: [
      { label: "Model Predictions", icon: "🧠", route: "model-predictions", permission: "forecasting:view" },
      { label: "Reports", icon: "📄", route: "reports", permission: "reports:view" },
      { label: "Alerts", icon: "🔔", route: "alerts", permission: "alerts:view" },
      { label: "Forecast & Trends", icon: "📈", route: "forecasting", permission: "forecasting:view" }
    ]
  },
  {
    title: "SYSTEM",
    items: [
      { label: "Users", icon: "👥", route: "users", permission: "users:view" },
      { label: "Roles & Permissions", icon: "♡", route: "roles", permission: "roles:view" },
      { label: "Audit Logs", icon: "📋", route: "audit-logs", permission: "audit_logs:view" },
      { label: "Settings", icon: "⚙", route: "settings", permission: "settings:view" }
    ]
  }
];

export function renderSidebar() {
  const sidebar = document.getElementById("sidebar");

  if (!sidebar) return;

  sidebar.innerHTML = `
    <nav id="sidebar-nav" class="sidebar-nav">
      ${MENU_GROUPS.map(group => {
        const allowedItems = group.items.filter(item => can(item.permission));

        if (!allowedItems.length) return "";

        return `
          <p class="sidebar-section-title">${group.title}</p>

          ${allowedItems.map(item => `
            <button data-nav="${item.route}" class="sidebar-link">
              <span>${item.icon}</span>
              <span>${item.label}</span>
            </button>
          `).join("")}
        `;
      }).join("")}
    </nav>
  `;
}