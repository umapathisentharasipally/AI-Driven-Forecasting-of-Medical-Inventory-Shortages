import { apiRequest } from "./api.client.js";

function asArray(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  return [];
}

export const userService = {
  async getUsers() {
    const payload = await apiRequest("/users/");
    return asArray(payload);
  },

  async createUser(payload) {
    return apiRequest("/users/", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  updateUser(id, payload) {
    return apiRequest(`/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  updateUserStatus(id, payload) {
    return apiRequest(`/users/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },

  deleteUser(id) {
    return apiRequest(`/users/${id}`, {
      method: "DELETE"
    });
  }
};