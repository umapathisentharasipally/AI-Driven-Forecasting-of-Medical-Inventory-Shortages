import { apiRequest } from "./api.client.js";

export const analyticsService = {
  getInventoryValueTrend(period = "7d") {
    return apiRequest(`/analytics/inventory-value-trend/?period=${period}`);
  },

  getStockoutRisk() {
    return apiRequest("/analytics/stockout-risk/");
  },

  getTopRiskItems() {
    return apiRequest("/analytics/top-risk-items/");
  },

  getPredictions() {
    return apiRequest("/analytics/predictions/");
  }
};