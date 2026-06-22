import { apiRequest } from "./api.client.js";
import { normalizeList } from "../utils/api-response.js";

export const categoryService = {
  async getCategories() {
    const response = await apiRequest("/categories/");
    return normalizeList(response);
  },

  createCategory(payload) {
    return apiRequest("/categories/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateCategory(id, payload) {
    return apiRequest(`/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteCategory(id) {
    return apiRequest(`/categories/${id}`, {
      method: "DELETE"
    });
  }
};