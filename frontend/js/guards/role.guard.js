import { authStore } from "../store/auth.store.js";

export function hasRoleAccess(allowedRoles = []) {
  const role = authStore.getRole();

  if (!allowedRoles.includes(role)) {
    location.hash = "#/dashboard";
    return false;
  }

  return true;
}