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