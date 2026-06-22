import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const vendorService = {
  async getVendors() {
    const response = await apiRequest("/vendors/");
    return normalizeList(response);
  },

  createVendor(payload) {
    return apiRequest("/vendors/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateVendor(id, payload) {
    return apiRequest(`/vendors/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteVendor(id) {
    return apiRequest(`/vendors/${id}`, {
      method: "DELETE"
    });
  }
};