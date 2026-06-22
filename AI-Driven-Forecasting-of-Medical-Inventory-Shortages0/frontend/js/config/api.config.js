import { CONFIG } from "../config/config.js";

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem(CONFIG.TOKEN_KEY);

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
export const CONFIG = {
  API_BASE_URL:
    window.MEDINV_CONFIG?.API_BASE_URL ||
    localStorage.getItem("MEDINV_API_URL") ||
    "http://127.0.0.1:8000/api/v1",

  TOKEN_KEY: "access_token",
  REFRESH_KEY: "refresh_token",
  ROLE_KEY: "role",

  APP_NAME: "MedInv Forecast"
};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    console.error("API Error:", data);
    throw new Error(
      data?.detail?.[0]?.msg ||
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}`
    );
  }

  return data;
}

export const request = apiRequest;