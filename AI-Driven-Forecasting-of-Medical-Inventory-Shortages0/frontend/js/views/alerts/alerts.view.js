import { alertService } from "../../services/alert.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let alerts = [];
let activeFilter = "all";

const filterMap = {
  all: "",
  critical: "critical",
  low_stock: "low_stock",
  expiring: "expiring",
  pending: "pending_approval"
};

function skeletonAlerts() {
  view.innerHTML = `
    <main class="alerts-page">
      <div class="alerts-header skeleton-box"></div>

      <section class="alert-summary-grid">
        <div class="alert-summary-card skeleton-card"></div>
        <div class="alert-summary-card skeleton-card"></div>
        <div class="alert-summary-card skeleton-card"></div>
      </section>

      <div class="alerts-card">
        ${Array.from({ length: 8 })
          .map(() => `<div class="skeleton-row"></div>`)
          .join("")}
      </div>
    </main>
  `;
}

function severityBadge(severity) {
  const map = {
    High: "badge-danger",
    Medium: "badge-warning",
    Low: "badge-info"
  };

  return `
    <span class="status-badge ${map[severity] || "badge-info"}">
      ${escapeHTML(severity)}
    </span>
  `;
}

function alertIcon(type) {
  const map = {
    critical: "🚨",
    low_stock: "⚠️",
    expiring: "⏳",
    pending_approval: "🕒",
    abnormal_consumption: "📈"
  };

  return map[type] || "🔔";
}

function alertTone(type) {
  const map = {
    critical: "danger",
    low_stock: "warning",
    expiring: "warning",
    pending_approval: "info",
    abnormal_consumption: "info"
  };

  return map[type] || "info";
}

function timeAgo(value) {
  if (!value) return "-";

  const date = new Date(value);
  const seconds =
    Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return "Just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;

  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
}

function countByType(type) {
  return alerts.filter(alert =>
    alert.type === type && !alert.dismissed
  ).length;
}

function renderSummaryCards() {
  return `
    <section class="alert-summary-grid">
      <article class="alert-summary-card danger">
        <div>
          <p>Critical Alerts</p>
          <h3>${countByType("critical")}</h3>
        </div>
        <span>🚨</span>
      </article>

      <article class="alert-summary-card warning">
        <div>
          <p>Low Stock Alerts</p>
          <h3>${countByType("low_stock")}</h3>
        </div>
        <span>⚠️</span>
      </article>

      <article class="alert-summary-card warning">
        <div>
          <p>Expiring Soon</p>
          <h3>${countByType("expiring")}</h3>
        </div>
        <span>⏳</span>
      </article>
    </section>
  `;
}

function renderTabs() {
  const tabs = [
    ["all", "All"],
    ["critical", "Critical"],
    ["low_stock", "Low Stock"],
    ["expiring", "Expiring"],
    ["pending", "Pending"]
  ];

  return `
    <div class="alerts-tabs">
      ${tabs.map(([key, label]) => `
        <button 
          data-alert-filter="${key}"
          class="${activeFilter === key ? "active" : ""}">
          ${label}
        </button>
      `).join("")}
    </div>
  `;
}

function filteredAlerts() {
  const apiType = filterMap[activeFilter];

  if (!apiType) {
    return alerts.filter(alert => !alert.dismissed);
  }

  return alerts.filter(alert =>
    alert.type === apiType && !alert.dismissed
  );
}

function renderAlertRows() {
  const rows = filteredAlerts();

  if (!rows.length) {
    return `
      <div class="empty-alerts">
        <strong>No alerts found</strong>
        <p>There are no active alerts for this filter.</p>
      </div>
    `;
  }

  return rows.map(alert => `
    <article 
      class="alert-list-row"
      data-alert-row="${alert.id}">
      
      <div class="alert-list-icon ${alertTone(alert.type)}">
        ${alertIcon(alert.type)}
      </div>

      <div class="alert-list-content">
        <div class="alert-list-title">
          <strong>${escapeHTML(alert.title)}</strong>
          ${severityBadge(alert.severity)}
        </div>

        <p>${escapeHTML(alert.description)}</p>

        <small>${timeAgo(alert.timestamp)}</small>
      </div>

      <button 
        class="dismiss-alert-btn"
        data-dismiss-alert="${alert.id}">
        Dismiss
      </button>
    </article>
  `).join("");
}

function renderAlertsPage() {
  view.innerHTML = `
    <main class="alerts-page">
      <section class="alerts-title-row">
        <div>
          <h1>Alerts</h1>
          <p>Monitor stock risks, expiry alerts, pending approvals, and abnormal consumption.</p>
        </div>
      </section>

      ${renderSummaryCards()}

      <section class="alerts-card">
        <div class="alerts-card-header">
          <h2>Active Alerts</h2>
          ${renderTabs()}
        </div>

        <div class="alerts-list">
          ${renderAlertRows()}
        </div>
      </section>
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  document.querySelectorAll("[data-alert-filter]").forEach(button => {
    button.addEventListener("click", async () => {
      activeFilter = button.dataset.alertFilter;
      await reloadAlerts();
    });
  });

  document.querySelectorAll("[data-dismiss-alert]").forEach(button => {
    button.addEventListener("click", async () => {
      await dismissAlert(button.dataset.dismissAlert);
    });
  });
}

async function dismissAlert(id) {
  const row =
    document.querySelector(`[data-alert-row="${id}"]`);

  if (row) {
    row.classList.add("alert-dismissing");
  }

  try {
    await alertService.dismissAlert(id);

    showToast(
      "Alert dismissed successfully",
      "success"
    );

    await reloadAlerts();

  } catch (error) {

    showToast(
      "Failed to dismiss alert",
      "error"
    );

    if (row) {
      row.classList.remove("alert-dismissing");
    }
  }
}

async function reloadAlerts() {
  const type =
    filterMap[activeFilter] || "";

  alerts =
    await alertService.getAlerts(type);

  renderAlertsPage();
}

export async function renderAlerts() {
  skeletonAlerts();

  alerts =
    await alertService.getAlerts();

  renderAlertsPage();
}