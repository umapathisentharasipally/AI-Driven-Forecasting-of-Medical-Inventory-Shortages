import { ROUTES } from "./routes.js";
import { can } from "../auth/permissions.js";
import {
  renderErrorView,
  renderNotFoundView
} from "../components/error-view.js";

export async function navigateTo(routeName) {
  const route = ROUTES[routeName];

  if (!route) {
    renderNotFoundView();
    return;
  }
  if (route.permission !== "public" && !can(route.permission)) {
    renderErrorView("You do not have permission to access this page.");
    return;
  }

  document.querySelectorAll("[data-nav]").forEach(item => {
    item.classList.toggle("active", item.dataset.nav === routeName);
  });

  try {
    await route.render();
  } catch (error) {
    console.error(error);
    renderErrorView(error.message);
  }
}