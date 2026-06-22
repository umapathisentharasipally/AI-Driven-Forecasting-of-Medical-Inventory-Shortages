import { alertService } from "../services/alert.service.js";

export async function initNotifications() {
  const button = document.getElementById("notificationBtn");
  const panel = document.getElementById("notificationPanel");
  const badge = document.getElementById("notificationBadge");

  if (!button || !panel) return;

  const alerts = await alertService.getAlerts();
  const activeAlerts = alerts.filter(alert => !alert.dismissed);

  if (badge) {
    badge.textContent = activeAlerts.length;
    badge.hidden = activeAlerts.length === 0;
  }

  panel.innerHTML = `
    <div class="notification-header">
      <strong>Notifications</strong>
    </div>

    ${activeAlerts.slice(0, 5).map(alert => `
      <article class="notification-item">
        <strong>${alert.title}</strong>
        <p>${alert.description}</p>
      </article>
    `).join("") || `<p class="notification-empty">No active notifications</p>`}
  `;

  button.addEventListener("click", () => {
    panel.classList.toggle("hidden");
  });
}