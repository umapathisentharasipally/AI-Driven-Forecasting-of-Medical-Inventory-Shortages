import { apiRequest } from "./api.client.js";

export const profileService = {
  getProfile() {
    return apiRequest("/auth/me");
  },

  updateProfile(payload) {
    return apiRequest("/profile/", {
      method: "PUT",
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