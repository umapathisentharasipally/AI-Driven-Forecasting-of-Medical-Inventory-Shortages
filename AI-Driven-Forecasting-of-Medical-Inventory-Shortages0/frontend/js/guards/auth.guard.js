import { authStore } from "../store/auth.store.js";

export function requireAuth() {
  if (!authStore.isAuthenticated()) {
    location.hash = "#/login";
    return false;
  }

  return true;
}