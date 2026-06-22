import { apiRequest } from "./api.client.js";

function unwrap(response) {
  return response?.data || response || {};
}

function list(response) {
  const data = unwrap(response);
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.items)) return data.items;
  return [];
}

export const dashboardService = {
  async getAdminDashboard() {
    const response = await apiRequest("/dashboard/admin");
    return unwrap(response);
  },

  async getInventoryStats() {
    const data = await this.getAdminDashboard();
    const metrics = data.metrics || {};

    return {
      total_items: metrics.total_inventory_items || 0,
      total_value: metrics.total_inventory_value || 0,
      low_stock: metrics.low_stock_items || 0,
      stockout_risk_high: metrics.high_stockout_risk || 0,
      active_alerts: metrics.active_alerts || 0,
      critical_items: metrics.critical_items || 0
    };
  },

  async getInventoryValueTrend() {
    const response = await apiRequest("/dashboard/charts?days=30");
    const data = unwrap(response);

    return {
      labels: data.inventory_value_trend?.labels || [],
      values: data.inventory_value_trend?.values || []
    };
  },

  async getStockoutRisk() {
    const data = await this.getAdminDashboard();
    const risk = data.risk_distribution || data.stockout_risk_distribution || {};

    return {
      high: {
        count: risk.high?.count || data.metrics?.high_stockout_risk || 0,
        percentage: risk.high?.percentage || 0
      },
      medium: {
        count: risk.medium?.count || 0,
        percentage: risk.medium?.percentage || 0
      },
      low: {
        count: risk.low?.count || 0,
        percentage: risk.low?.percentage || 0
      }
    };
  },

  async getTopRiskItems() {
    const data = await this.getAdminDashboard();
    const items = data.top_risk_items || [];

    return items.map(item => ({
      name: item.item_name || item.item_id || "Unknown Item",
      category: item.category || item.item_category || "-",
      risk_level: item.risk_level || "High",
      stockout_probability: Number(item.stockout_probability || 0)
    }));
  },

  async getAlerts() {
    const data = await this.getAdminDashboard();
    const alerts = data.recent_alerts || [];

    return alerts.map(alert => ({
      title: alert.title || alert.alert_type || "Alert",
      description: alert.message || alert.description || "-",
      severity: alert.severity || alert.risk_level || "Medium"
    }));
  },

  async getCategories() {
    const data = await this.getAdminDashboard();
    const categories = data.category_distribution || [];

    return categories.map(item => ({
      name: item.name || item._id || "Uncategorized",
      item_count: item.value || item.count || 0,
      percentage: item.percentage || 0
    }));
  },

  async getPredictions() {
    const data = await this.getAdminDashboard();
    const predictions = data.recent_predictions || [];

    return predictions.map(item => ({
      name: item.item_name || item.item_id || "Unknown Item",
      facility: item.facility_name || item.facility_id || "-",
      predicted_date: item.prediction_date || "-",
      risk_level: item.risk_level || "Medium"
    }));
  },

  async getSystemStats() {
    const data = await this.getAdminDashboard();
    const metrics = data.metrics || {};
    const status = data.system_status || {};

    return {
      facilities: metrics.facilities || 0,
      vendors: metrics.vendors || 0,
      departments: metrics.departments || 0,
      users: metrics.users || 0,
      system_status: status.status || "Operational"
    };
  }
};