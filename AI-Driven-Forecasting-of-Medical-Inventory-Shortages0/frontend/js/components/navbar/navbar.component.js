import { authStore } from "../../store/auth.store.js";

export function Navbar() {
  const user = authStore.getUser() || {
    name: "Admin User"
  };

  return `
    <header class="navbar">
      <div class="navbar-title">
        <h1>Welcome back, ${user.name}! 👋</h1>
        <p>Here’s what's happening with your shipments today.</p>
      </div>

      <div class="navbar-actions">
        <div class="nav-pill">📅 May 20, 2025 • 10:30 AM</div>

        <button class="notification-btn">
          🔔
          <span class="notification-count">5</span>
        </button>

        <div class="nav-avatar"></div>
      </div>
    </header>
  `;
}