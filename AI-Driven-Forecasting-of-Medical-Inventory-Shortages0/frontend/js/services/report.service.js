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

  generateReport(payload) {
    return apiRequest("/reports/generate", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  downloadReport(id) {
    return apiRequest(`/reports/${id}/download`);
  }
};