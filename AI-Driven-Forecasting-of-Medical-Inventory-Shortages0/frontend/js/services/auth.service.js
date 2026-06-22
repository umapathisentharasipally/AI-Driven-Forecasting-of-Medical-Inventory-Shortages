import { apiRequest } from "./api.client.js";

export const authService = {
  login(payload) {
    return apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: payload.username,
        password: payload.password
      })
    });
  },

  me() {
    return apiRequest("/auth/me");
  },

  logout() {
    return apiRequest("/auth/logout", {
      method: "POST"
    });
  }
};