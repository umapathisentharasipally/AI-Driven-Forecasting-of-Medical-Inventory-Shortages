export const APP_NAME = "MedInv Forecast";

export const API_PREFIX = "/api/v1";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  ROLE: "role",
  THEME: "med_theme",
  USER: "med_user"
};

export const ROUTE_NAMES = {
  DASHBOARD: "dashboard",
  INVENTORY: "inventory",
  CATEGORIES: "categories",
  VENDORS: "vendors",
  PURCHASE_ORDERS: "purchase-orders",
  STOCK_RECEIPTS: "stock-receipts",
  STOCK_TRANSFERS: "stock-transfers",
  ALERTS: "alerts",
  FORECASTING: "forecasting",
  REPORTS: "reports",
  USERS: "users",
  ROLES: "roles",
  AUDIT_LOGS: "audit-logs",
  SETTINGS: "settings"
};

export const STATUS = {
  IN_STOCK: "In Stock",
  LOW_STOCK: "Low Stock",
  OUT_OF_STOCK: "Out of Stock",
  EXPIRED: "Expired",
  PENDING: "Pending",
  APPROVED: "Approved",
  SHIPPED: "Shipped",
  RECEIVED: "Received"
};

export const RISK_LEVELS = {
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low"
};

export const ALERT_TYPES = {
  CRITICAL: "critical",
  LOW_STOCK: "low_stock",
  EXPIRING: "expiring",
  PENDING_APPROVAL: "pending_approval",
  ABNORMAL_CONSUMPTION: "abnormal_consumption"
};

export const USER_ROLES = {
  SUPER_ADMIN: "super_admin",
  ADMIN: "admin",
  SUPPLY_MANAGER: "supply_manager",
  INVENTORY_MANAGER: "inventory_manager",
  ANALYST: "analyst",
  PHARMACIST: "pharmacist",
  VIEWER: "viewer"
};

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 10,
  INVENTORY_PAGE_SIZE: 15
};

export const CHART_COLORS = {
  PRIMARY: "#4F46E5",
  INDIGO: "#818CF8",
  SUCCESS: "#10B981",
  WARNING: "#F59E0B",
  DANGER: "#EF4444",
  BLUE: "#3B82F6",
  MUTED: "#94A3B8"
};

export const CATEGORY_COLORS = [
  "#6366F1",
  "#F59E0B",
  "#10B981",
  "#3B82F6",
  "#94A3B8"
];

export const THEME = {
  DARK: "dark",
  LIGHT: "light"
};

export const DATE_PERIODS = {
  SEVEN_DAYS: "7d",
  THIRTY_DAYS: "30d",
  THREE_MONTHS: "3m"
};

export const API_ENDPOINTS = {
  AUTH_LOGIN: "/auth/login",
  AUTH_ME: "/auth/me",

  INVENTORY: "/inventory/",
  INVENTORY_STATS: "/inventory/stats/",
  INVENTORY_LOW_STOCK: "/inventory/low-stock/",
  INVENTORY_EXPIRING: "/inventory/expiring/",

  CATEGORIES: "/categories/",
  VENDORS: "/vendors/",
  DEPARTMENTS: "/departments/",

  PURCHASE_ORDERS: "/purchase-orders/",
  STOCK_RECEIPTS: "/stock-receipts/",
  STOCK_TRANSFERS: "/stock-transfers/",

  ALERTS: "/alerts/",
  NOTIFICATIONS: "/notifications/",

  INVENTORY_VALUE_TREND: "/analytics/inventory-value-trend/",
  STOCKOUT_RISK: "/analytics/stockout-risk/",
  TOP_RISK_ITEMS: "/analytics/top-risk-items/",
  PREDICTIONS: "/analytics/predictions/",

  REPORTS: "/reports/",
  USERS: "/users/",
  ROLES: "/roles/",
  AUDIT_LOGS: "/audit-logs/",
  SECURITY_LOGS: "/security-logs/",
  SETTINGS: "/settings/",
  SYSTEM_STATS: "/system/stats/",
  SYSTEM_STATUS: "/system/status/",
  HEALTH: "/health"
};