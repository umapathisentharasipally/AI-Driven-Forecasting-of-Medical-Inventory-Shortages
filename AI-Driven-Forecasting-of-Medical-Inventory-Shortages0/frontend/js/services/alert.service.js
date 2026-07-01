import { apiRequest } from "./api.client.js";
import { normalizeList, normalizeObject } from "../utils/api-response.js";

function unwrap(response) {
  return response?.data || response || {};
}

export const analyticsService = {
  async getInventoryValueTrend(period = "7d") {
    const response = await apiRequest(`/analytics/inventory-value-trend/?period=${period}`);
    const data = normalizeList(response);

    return {
      labels: data.map(item => item.date),
      values: data.map(item => Number(item.value || 0))
    };
  },

  async getStockoutRisk() {
    const response = await apiRequest("/analytics/stockout-risk/");
    const data = unwrap(response);

    const high = Number(data.high || 0);
    const medium = Number(data.medium || 0);
    const low = Number(data.low || 0);
    const total = high + medium + low;

    return {
      total,
      high: {
        count: high,
        percentage: total ? ((high / total) * 100).toFixed(2) : 0
      },
      medium: {
        count: medium,
        percentage: total ? ((medium / total) * 100).toFixed(2) : 0
      },
      low: {
        count: low,
        percentage: total ? ((low / total) * 100).toFixed(2) : 0
      }
    };
  },

  async getTopRiskItems() {
    const response = await apiRequest("/analytics/top-risk-items/?limit=10");
    const rows = normalizeList(response);

    return rows.map(item => ({
      id: item.id || item._id,
      name: item.item_name || item.item_id || "Unknown Item",
      category: item.item_category || item.category || "-",
      risk_level: item.risk_level || "Low",
      stockout_probability: Number(item.stockout_probability || 0),
      current_stock: Number(item.current_stock_on_hand || 0),
      safety_stock: Number(item.safety_stock_level || 0),
      predicted_date: item.prediction_date
    }));
  },

  async getPredictions(page = 1, limit = 20) {
    const response = await apiRequest(`/predictions/?page=${page}&limit=${limit}`);
    const rows = normalizeList(response);

    return rows.map(item => ({
      id: item.id || item._id,
      name: item.item_name || item.item_id || "Unknown Item",
      facility: item.facility_name || item.facility_id || "-",
      predicted_date: item.prediction_date || item.created_at,
      risk_level: item.risk_level || "Low",
      stockout_probability: Number(item.stockout_probability || 0),
      model_name: item.model_name || "xgboost",
      model_version: item.model_version || "unknown"
    }));
  },

  async runBatchPredictions(payload = { run_all: true }) {
    const response = await apiRequest("/predictions/batch", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    return normalizeObject(response);
  }
};