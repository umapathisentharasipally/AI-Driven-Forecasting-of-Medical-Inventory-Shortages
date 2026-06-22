import { apiRequest } from "./api.client.js";
import { normalizeList, normalizeObject } from "../utils/api-response.js";

export const inventoryService = {
  async getItems() {
    const response = await apiRequest("/inventory/");
    return normalizeList(response);
  },

  async getItem(id) {
    const response = await apiRequest(`/inventory/${id}`);
    return normalizeObject(response);
  },

  createItem(payload) {
    return apiRequest("/inventory/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateItem(id, payload) {
    return apiRequest(`/inventory/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteItem(id) {
    return apiRequest(`/inventory/${id}`, {
      method: "DELETE"
    });
  },

  adjustStock(id, payload) {
    return apiRequest(`/inventory/${id}/stock`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  async getBelowSafetyStock() {
    const response = await apiRequest("/inventory/below-safety-stock");
    return normalizeList(response);
  },

  async getExpiringSoon(days = 30) {
    const response = await apiRequest(`/inventory/expiring-soon?days=${days}`);
    return normalizeList(response);
  }
};