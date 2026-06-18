import { authStore } from "../../store/auth.store.js";

const menus = {
  "Admin User": [
    ["#/dashboard", "▣", "Dashboard"],
    ["#/create-shipment", "□", "Create Shipment"],
    ["#/my-shipments", "▤", "My Shipments"],
    ["#/device-stream", "≋", "Device Stream"],
    ["#/notifications", "♢", "Notifications"],
    ["#/profile", "○", "Profile"],
    ["#/settings", "⚙", "Settings"]
  ],
  Admin: [
    ["#/dashboard", "▣", "Dashboard"],
    ["#/users", "♙", "Users"],
    ["#/create-user", "+", "Create User"],
    ["#/shipments", "▤", "Shipments"],
    ["#/analytics", "◌", "Analytics"],
    ["#/monitoring", "◎", "Monitoring"],
    ["#/profile", "○", "Profile"]
  ],
  "Super Admin": [
    ["#/dashboard", "▣", "Dashboard"],
    ["#/admins", "♙", "Admins"],
    ["#/users", "♙", "Users"],
    ["#/shipments", "▤", "Shipments"],
    ["#/devices", "▥", "Devices"],
    ["#/analytics", "◌", "Analytics"],
    ["#/security-logs", "◈", "Security Logs"],
    ["#/settings", "⚙", "Settings"]
  ]
};

export function Sidebar() {
  const role = authStore.getRole();
  const user = authStore.getUser() || {
    name: "Admin User",
    email: "adminuser@email.com"
  };

  const currentHash = location.hash || "#/dashboard";
  const menu = menus[role] || menus["Admin User"];

  return `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">⬡</div>
        <div class="brand-text">SCMXPERT <span>LITE</span></div>
      </div>

      <nav class="sidebar-menu">
        ${menu.map(([href, icon, label]) => `
          <a class="sidebar-link ${currentHash === href ? "active" : ""}" href="${href}">
            <span>${icon}</span>
            <span>${label}</span>
          </a>
        `).join("")}

        <a class="sidebar-link logout" href="#/logout">
          <span>↪</span>
          <span>Logout</span>
        </a>
      </nav>

      <div class="sidebar-footer">
        <div class="user-avatar"></div>
        <div>
          <div class="user-name">${user.name}</div>
          <div>${user.email}</div>
          <div class="user-status">● Online</div>
        </div>
      </div>
    </aside>
  `;
}