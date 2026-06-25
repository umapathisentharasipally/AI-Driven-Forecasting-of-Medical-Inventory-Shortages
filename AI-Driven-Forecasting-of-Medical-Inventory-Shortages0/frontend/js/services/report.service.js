import { apiRequest } from "./api.client.js";
import { normalizeList, normalizeObject } from "../utils/api-response.js";

function buildQuery(params = {}) {
  const query = new URLSearchParams(params).toString();
  return query ? `?${query}` : "";
}

export const reportService = {
  async getReports(params = {}) {
    const response = await apiRequest(`/reports/${buildQuery(params)}`);
    return normalizeList(response);
  },

  async getReport(id) {
    const response = await apiRequest(`/reports/${id}`);
    return normalizeObject(response);
  },

  async getInventorySummary(params = {}) {
    const response = await apiRequest(`/reports/${buildQuery({
      ...params,
      report_type: "inventory-summary"
    })}`);
    return normalizeList(response);
  },

  async getStockoutRiskReport(params = {}) {
    const response = await apiRequest(`/reports/${buildQuery({
      ...params,
      report_type: "stockout-risk"
    })}`);
    return normalizeList(response);
  },

  async getExpiryReport(params = {}) {
    const response = await apiRequest(`/reports/${buildQuery({
      ...params,
      report_type: "expiry"
    })}`);
    return normalizeList(response);
  },

  async getPredictionReport(params = {}) {
    const response = await apiRequest(`/reports/${buildQuery({
      ...params,
      report_type: "predictions"
    })}`);
    return normalizeList(response);
  },

  generateReport(payload) {
    return apiRequest("/reports/generate", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  downloadReport(id) {
    return apiRequest(`/reports/${id}/download`);
  },

  exportCsv(reportType, params = {}) {
    return apiRequest(`/reports/export/csv${buildQuery({
      ...params,
      report_type: reportType
    })}`);
  },

  exportPdf(reportType, params = {}) {
    return apiRequest(`/reports/export/pdf${buildQuery({
      ...params,
      report_type: reportType
    })}`);
  }
};