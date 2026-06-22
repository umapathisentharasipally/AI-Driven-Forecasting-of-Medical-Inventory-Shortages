import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const stockReceiptService = {
  async getReceipts() {
    const response = await apiRequest("/receipts/");
    return normalizeList(response);
  },

  async getRecentReceipts() {
    const response = await apiRequest("/receipts/recent");
    return normalizeList(response);
  },

  createReceipt(payload) {
    return apiRequest("/receipts/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
};