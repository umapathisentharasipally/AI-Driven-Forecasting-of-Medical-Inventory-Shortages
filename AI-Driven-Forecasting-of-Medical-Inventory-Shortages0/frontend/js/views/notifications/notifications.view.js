import { notificationService } from "../../services/notification.service.js";
import { escapeHTML } from "../../utils/dom.js";
import { timeAgo } from "../../utils/date.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let notifications = [];

function skeletonNotifications() {
  view.innerHTML = `
    <main class="notifications-page">
      <div class="skeleton-box"></div>
      ${Array.from({ length: 6 }).map(() => `<div class="skeleton-row"></div>`).join("")}
    </main>
  `;
}

function renderNotificationsPage() {
  view.innerHTML = `
    <main class="notifications-page">
      <section class="crud-title-row">
        <div>
          <h1>Notifications</h1>
          <p>Review system messages, inventory alerts, approvals, and updates.</p>
        </div>
      </section>

      <section class="notifications-list">
        ${
          notifications.length
            ? notifications.map(renderNotification).join("")
            : `<div class="empty-row">No notifications found</div>`
        }
      </section>
    </main>
  `;

  bindEvents();
}

function renderNotification(item) {
  return `
    <article class="notification-card ${item.is_read ? "read" : "unread"}">
      <div>
        <strong>${escapeHTML(item.title)}</strong>
        <p>${escapeHTML(item.message || item.description || "")}</p>
        <small>${timeAgo(item.created_at || item.timestamp)}</small>
      </div>

      ${
        item.is_read
          ? `<span class="status-badge badge-muted">Read</span>`
          : `<button class="primary-btn small" data-read="${item.id}">Mark Read</button>`
      }
    </article>
  `;
}

function bindEvents() {
  document.querySelectorAll("[data-read]").forEach(button => {
    button.addEventListener("click", async () => {
      try {
        await notificationService.markAsRead(button.dataset.read);
        showToast("Notification marked as read", "success");
        await reloadNotifications();
      } catch {
        showToast("Failed to update notification", "error");
      }
    });
  });
}

async function reloadNotifications() {
  notifications = await notificationService.getNotifications();
  renderNotificationsPage();
}

export async function renderNotifications() {
  skeletonNotifications();

  try {
    notifications = await notificationService.getNotifications();
    renderNotificationsPage();
  } catch {
    view.innerHTML = `<div class="error-state">Failed to load notifications.</div>`;
  }
}