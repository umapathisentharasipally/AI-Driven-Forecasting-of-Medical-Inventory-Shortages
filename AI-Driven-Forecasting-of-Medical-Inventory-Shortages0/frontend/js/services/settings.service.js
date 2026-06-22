import { apiRequest } from "./api.client.js";
import { normalizeObject } from "../utils/api-response.js";

export const settingsService = {
  async getSettings() {
    const response = await apiRequest("/settings/");
    return normalizeObject(response);
  },

  updateSettings(payload) {
    return apiRequest("/settings/", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  async getProfile() {
    const response = await apiRequest("/auth/me");
    return normalizeObject(response);
  },

  updateProfile(payload) {
    return apiRequest("/users/profile", {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  changePassword(payload) {
    return apiRequest("/auth/change-password", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
};