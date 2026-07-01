import { CONFIG } from "../config/config.js";
import { apiRequest } from "../services/api.client.js";

export function saveSession(data) {
  localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
  localStorage.setItem(CONFIG.REFRESH_KEY, data.refresh_token);
  localStorage.setItem(CONFIG.ROLE_KEY, normalizeRole(data.role));

  if (data.user) {
    localStorage.setItem("med_user", JSON.stringify(data.user));
  }
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem(CONFIG.TOKEN_KEY));
}

/**
 * Verify that the stored token is actually valid by calling the backend
 * This prevents accessing the app with a stale/expired token
 */
export async function isTokenValid() {
  try {
    if (!isAuthenticated()) {
      return false;
    }

    // Make a request to the /auth/me endpoint which requires valid token
    const response = await fetch(`${window.MEDINV_CONFIG?.API_BASE_URL || "/api/v1"}/auth/me`, {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem(CONFIG.TOKEN_KEY)}`,
        "Content-Type": "application/json"
      }
    });

    // If 401, token is invalid
    if (response.status === 401) {
      clearSession();
      return false;
    }

    // If any other error, also clear session
    if (!response.ok) {
      clearSession();
      return false;
    }

    return true;
  } catch (error) {
    console.error("Token validation error:", error);
    clearSession();
    return false;
  }
}

export function clearSession() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.REFRESH_KEY);
  localStorage.removeItem(CONFIG.ROLE_KEY);
  localStorage.removeItem("med_user");
}

export function normalizeRole(role) {
  return String(role || "viewer").toLowerCase().replaceAll(" ", "_");
}

export function redirectToApp() {
  window.location.hash = "#dashboard";
}

export function redirectByRole(role) {
  const routeMap = {
    super_admin: "dashboard",
    admin: "dashboard",
    supply_manager: "dashboard",
    inventory_manager: "inventory",
    analyst: "forecasting",
    pharmacist: "inventory",
    viewer: "dashboard"
  };

  window.location.hash = `#${routeMap[normalizeRole(role)] || "dashboard"}`;
  window.location.reload();
}
export function logout() {
  clearSession();
  // Reload to ensure clean state
  window.location.hash = "#login";
  window.location.reload();
}