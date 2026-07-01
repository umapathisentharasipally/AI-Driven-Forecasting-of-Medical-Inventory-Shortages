export const CONFIG = {
  API_BASE_URL:
    window.MEDINV_CONFIG?.API_BASE_URL ||
    "/api/v1",

  TOKEN_KEY: "access_token",
  REFRESH_KEY: "refresh_token",
  ROLE_KEY: "role",

  APP_NAME: "MedInv Forecast"
};