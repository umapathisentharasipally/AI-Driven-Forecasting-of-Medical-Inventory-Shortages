import { apiRequest } from "./api.client.js";

export const returnService = {
  getReturns() {
    return apiRequest("/returns/");
  },

  createReturn(payload) {
    return apiRequest("/returns/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateReturnStatus(id, payload) {
    return apiRequest(`/returns/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  }
};