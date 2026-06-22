import { CONFIG } from "../config/config.js";

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
  window.location.hash = "#login";
  window.location.reload();
}