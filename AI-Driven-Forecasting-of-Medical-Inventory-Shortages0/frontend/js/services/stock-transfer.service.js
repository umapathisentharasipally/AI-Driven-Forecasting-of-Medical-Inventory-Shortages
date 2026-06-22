import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const stockTransferService = {
  async getStockTransfers() {
    const response = await apiRequest("/transfers/");
    return normalizeList(response);
  },

  createStockTransfer(payload) {
    return apiRequest("/transfers/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  approveTransfer(id) {
    return apiRequest(`/transfers/${id}/approve`, {
      method: "PATCH"
    });
  },

  completeTransfer(id) {
    return apiRequest(`/transfers/${id}/complete`, {
      method: "PATCH"
    });
  }
};