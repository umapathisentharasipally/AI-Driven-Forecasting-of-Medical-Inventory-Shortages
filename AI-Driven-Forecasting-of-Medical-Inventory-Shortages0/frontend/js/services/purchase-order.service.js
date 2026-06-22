import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const purchaseOrderService = {
  async getPurchaseOrders() {
    const response = await apiRequest("/purchase-orders/");
    return normalizeList(response);
  },

  createPurchaseOrder(payload) {
    return apiRequest("/purchase-orders/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updatePurchaseOrder(id, payload) {
    return apiRequest(`/purchase-orders/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  }
};