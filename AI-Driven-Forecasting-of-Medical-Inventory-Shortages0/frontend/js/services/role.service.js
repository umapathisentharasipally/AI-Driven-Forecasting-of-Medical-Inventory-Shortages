import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const roleService = {
  async getRoles() {
    const response = await apiRequest("/roles/");
    return normalizeList(response);
  },

  async getPermissions() {
    const response = await apiRequest("/roles/permissions/");
    return normalizeList(response);
  },

  createRole(payload) {
    return apiRequest("/roles/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateRole(id, payload) {
    return apiRequest(`/roles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteRole(id) {
    return apiRequest(`/roles/${id}`, {
      method: "DELETE"
    });
  }
};