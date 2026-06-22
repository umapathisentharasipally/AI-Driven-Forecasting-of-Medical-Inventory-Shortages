import { renderSidebar } from "./sidebar.js";
import { renderNavbar } from "./navbar.js";

export function renderLayout() {
  renderSidebar();
  renderNavbar();
}