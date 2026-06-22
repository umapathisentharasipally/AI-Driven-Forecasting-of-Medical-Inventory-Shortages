import { isAuthenticated } from "./auth/session.js";
import { navigateTo } from "./router/router.js";
import { renderLayout } from "./layout/layout.js";
import { applySavedTheme, toggleTheme } from "./components/theme.js";
import { initGlobalSearch } from "./components/global-search.js";
import { initNotifications } from "./components/notifications.js";
import { initProfileMenu } from "./components/profile-menu.js";

document.addEventListener("DOMContentLoaded", async () => {
  applySavedTheme();

  document.addEventListener("click", async event => {
    const navItem = event.target.closest("[data-nav]");

    if (navItem) {
      await navigateTo(navItem.dataset.nav);
    }

    const themeBtn = event.target.closest("[data-theme-toggle]");

    if (themeBtn) {
      const theme = toggleTheme();
      themeBtn.textContent = theme === "dark" ? "🌙" : "☀️";

      const activeRoute =
        document.querySelector("[data-nav].active")?.dataset.nav || "dashboard";

      await navigateTo(activeRoute);
    }
  });

  if (!isAuthenticated()) {
    hideAppShell();
    await navigateTo("login");
    return;
  }

  showAppShell();
  renderLayout();

  initGlobalSearch();
  await initNotifications();
  await initProfileMenu();

  const initialRoute =
    localStorage.getItem("initial_route") ||
    location.hash.replace("#", "") ||
    "dashboard";

  localStorage.removeItem("initial_route");

  await navigateTo(initialRoute);
});

function hideAppShell() {
  document.getElementById("sidebar").style.display = "none";
  document.getElementById("navbar").style.display = "none";

  const mainLayout = document.querySelector(".main-layout");
  mainLayout.style.marginLeft = "0";
  mainLayout.style.width = "100%";
}

function showAppShell() {
  document.getElementById("sidebar").style.display = "";
  document.getElementById("navbar").style.display = "";

  const mainLayout = document.querySelector(".main-layout");
  mainLayout.style.marginLeft = "";
  mainLayout.style.width = "";
}