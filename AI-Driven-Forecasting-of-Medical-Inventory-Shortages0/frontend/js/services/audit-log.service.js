import { apiRequest } from "./api.client.js";

export const auditLogService = {
  getAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/audit-logs/${query ? `?${query}` : ""}`);
  },

  getSecurityLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/security-logs/${query ? `?${query}` : ""}`);
  }
};