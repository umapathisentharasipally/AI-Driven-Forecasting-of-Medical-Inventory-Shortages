import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const departmentService = {
  async getDepartments() {
    const response = await apiRequest("/departments/");
    return normalizeList(response);
  },

  createDepartment(payload) {
    return apiRequest("/departments/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateDepartment(id, payload) {
    return apiRequest(`/departments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteDepartment(id) {
    return apiRequest(`/departments/${id}`, {
      method: "DELETE"
    });
  }
};