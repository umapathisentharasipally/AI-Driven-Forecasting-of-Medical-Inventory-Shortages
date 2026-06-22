import { apiRequest } from "./api.client.js";

function asArray(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  return [];
}

function normalizeAlert(alert) {
  return {
    ...alert,
    type: alert.type || alert.alert_type,
    title: alert.title || alert.message || "Alert",
    description: alert.description || alert.message || "-",
    timestamp: alert.timestamp || alert.created_at,
    dismissed: alert.dismissed ?? ["resolved", "acknowledged"].includes(alert.status)
  };
}

export const alertService = {
  async getAlerts(type = "") {
    const query = type ? `?alert_type=${encodeURIComponent(type)}` : "";
    const payload = await apiRequest(`/alerts/${query}`);
    return asArray(payload).map(normalizeAlert);
  },

  dismissAlert(id) {
    return apiRequest(`/alerts/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: "resolved" })
    });
  }
};