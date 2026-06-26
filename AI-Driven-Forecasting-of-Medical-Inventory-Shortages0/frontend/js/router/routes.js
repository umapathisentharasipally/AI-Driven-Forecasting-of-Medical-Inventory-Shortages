import { renderDashboard } from "../views/dashboard/dashboard.view.js";
import { renderInventory } from "../views/inventory/inventory.view.js";
import { renderCategories } from "../views/categories/categories.view.js";
import { renderVendors } from "../views/vendors/vendors.view.js";
import { renderPurchaseOrders } from "../views/purchase-orders/purchase-orders.view.js";
import { renderStockTransfers } from "../views/stock-transfers/stock-transfers.view.js";
import { renderStockReceipts } from "../views/stock-receipts/stock-receipts.view.js";
import { renderForecasting } from "../views/forecasting/forecasting.view.js";
import { renderReports } from "../views/reports/reports.view.js";
import { renderAlerts } from "../views/alerts/alerts.view.js";
import { renderUsers } from "../views/users/users.view.js";
import { renderRoles } from "../views/users/roles.view.js";
import { renderAuditLogs } from "../views/audit-logs/audit-logs.view.js";
import { renderSettings } from "../views/settings/settings.view.js";
import { renderLogin } from "../views/auth/login.view.js";


export const ROUTES = {
  login: {
    permission: "public",
    render: renderLogin
  },
  dashboard: {
    permission: "dashboard:view",
    render: renderDashboard
  },

  inventory: {
    permission: "inventory:view",
    render: renderInventory
  },

  categories: {
    permission: "categories:view",
    render: renderCategories
  },

  vendors: {
    permission: "vendors:view",
    render: renderVendors
  },

  "purchase-orders": {
    permission: "purchase_orders:view",
    render: renderPurchaseOrders
  },

  "stock-transfers": {
    permission: "stock_transfers:view",
    render: renderStockTransfers
  },

  "stock-receipts": {
    permission: "receipts:view",
    render: renderStockReceipts
  },

  forecasting: {
    permission: "forecasting:view",
    render: renderForecasting
  },

  reports: {
    permission: "reports:view",
    render: renderReports
  },
  "model-predictions": {
    permission: "forecasting:view",
    render: renderForecasting
  },

  alerts: {
    permission: "alerts:view",
    render: renderAlerts
  },

  users: {
    permission: "users:view",
    render: renderUsers
  },

  roles: {
    permission: "roles:view",
    render: renderRoles
  },

  "audit-logs": {
    permission: "audit_logs:view",
    render: renderAuditLogs
  },

  settings: {
    permission: "settings:view",
    render: renderSettings
  }
};