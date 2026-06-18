import { API_BASE_URL } from "../config/api.config.js";
import { authStore } from "../store/auth.store.js";
import { showToast } from "../components/toasts/toast.component.js";

export async function apiRequest(path, options = {}) {
  const token = authStore.getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      authStore.clear();
      location.hash = "#/login";
      showToast("Session expired. Please login again.", "error");
      return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(data?.detail || "Request failed");
    }

    return data;
  } catch (error) {
    showToast(error.message || "Network error", "error");
    throw error;
  }
}