import { request } from "../services/api.js";

export async function checkBackendHealth() {
  try {
    const response = await request("/health");

    return {
      online: true,
      status: response.status || "ok"
    };

  } catch (error) {
    return {
      online: false,
      status: "offline",
      message: error.message
    };
  }
}