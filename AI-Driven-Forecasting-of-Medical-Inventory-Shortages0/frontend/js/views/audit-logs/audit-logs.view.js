import { auditLogService } from "../../services/audit-log.service.js";
import { $, escapeHTML } from "../../utils/dom.js";

const view = document.getElementById("app");

let auditLogs = [];
let securityLogs = [];
let activeTab = "audit";
let filters = {
  user: "",
  action: "",
  from_date: "",
  to_date: ""
};

function skeletonLogs() {
  view.innerHTML = `
    <main class="system-page">
      <div class="skeleton-box"></div>
      <div class="system-card">
        ${Array.from({ length: 10 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function formatDateTime(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function statusBadge(value) {
  const map = {
    success: "badge-success",
    failed: "badge-danger",
    warning: "badge-warning",
    info: "badge-info"
  };

  return `<span class="status-badge ${map[String(value).toLowerCase()] || "badge-info"}">${escapeHTML(value)}</span>`;
}

function renderHeader() {
  return `
    <section class="system-title-row">
      <div>
        <h1>Audit Logs</h1>
        <p>Track user activity, security events, and operational changes.</p>
      </div>
    </section>
  `;
}

function renderTabs() {
  return `
    <section class="system-tabs">
      <button class="${activeTab === "audit" ? "active" : ""}" data-log-tab="audit">
        Audit Logs
      </button>

      <button class="${activeTab === "security" ? "active" : ""}" data-log-tab="security">
        Security Logs
      </button>
    </section>
  `;
}

function renderFilters() {
  return `
    <section class="system-filter-bar">
      <input id="filterUser" value="${escapeHTML(filters.user)}" placeholder="Filter by user..." />

      <input id="filterAction" value="${escapeHTML(filters.action)}" placeholder="Filter by action..." />

      <input id="filterFromDate" value="${escapeHTML(filters.from_date)}" type="date" />

      <input id="filterToDate" value="${escapeHTML(filters.to_date)}" type="date" />

      <button id="applyLogFilters" class="primary-btn">
        Apply Filters
      </button>
    </section>
  `;
}

function renderAuditTable() {
  return `
    <section class="system-card">
      <div class="table-wrapper">
        <table class="system-table">
          <thead>
            <tr>
              <th>#</th>
              <th>User</th>
              <th>Action</th>
              <th>Module</th>
              <th>Entity</th>
              <th>IP Address</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>

          <tbody>
            ${
              auditLogs.length
                ? auditLogs.map((log, index) => `
                  <tr>
                    <td>${index + 1}</td>
                    <td>
                      <strong>${escapeHTML(log.user_name || "-")}</strong>
                      <small>${escapeHTML(log.user_email || "")}</small>
                    </td>
                    <td>${escapeHTML(log.action)}</td>
                    <td>${escapeHTML(log.module || "-")}</td>
                    <td>${escapeHTML(log.entity_id || "-")}</td>
                    <td><code>${escapeHTML(log.ip_address || "-")}</code></td>
                    <td>${statusBadge(log.status || "success")}</td>
                    <td>${formatDateTime(log.created_at || log.timestamp)}</td>
                  </tr>
                `).join("")
                : `<tr><td colspan="8" class="empty-row">No audit logs found</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderSecurityTable() {
  return `
    <section class="system-card">
      <div class="table-wrapper">
        <table class="system-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Event</th>
              <th>User</th>
              <th>IP Address</th>
              <th>User Agent</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>

          <tbody>
            ${
              securityLogs.length
                ? securityLogs.map((log, index) => `
                  <tr>
                    <td>${index + 1}</td>
                    <td><strong>${escapeHTML(log.event || log.action)}</strong></td>
                    <td>${escapeHTML(log.user_email || "-")}</td>
                    <td><code>${escapeHTML(log.ip_address || "-")}</code></td>
                    <td>${escapeHTML(log.user_agent || "-")}</td>
                    <td>${statusBadge(log.severity || "info")}</td>
                    <td>${statusBadge(log.status || "success")}</td>
                    <td>${formatDateTime(log.created_at || log.timestamp)}</td>
                  </tr>
                `).join("")
                : `<tr><td colspan="8" class="empty-row">No security logs found</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderLogsPage() {
  view.innerHTML = `
    <main class="system-page">
      ${renderHeader()}
      ${renderTabs()}
      ${renderFilters()}
      ${activeTab === "audit" ? renderAuditTable() : renderSecurityTable()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  document.querySelectorAll("[data-log-tab]").forEach(button => {
    button.addEventListener("click", async () => {
      activeTab = button.dataset.logTab;
      await loadLogs();
    });
  });

  $("#applyLogFilters").addEventListener("click", async () => {
    filters = {
      user: $("#filterUser").value,
      action: $("#filterAction").value,
      from_date: $("#filterFromDate").value,
      to_date: $("#filterToDate").value
    };

    await loadLogs();
  });
}

function cleanFilters() {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value)
  );
}

async function loadLogs() {
  skeletonLogs();

  if (activeTab === "audit") {
    auditLogs = await auditLogService.getAuditLogs(cleanFilters());
  } else {
    securityLogs = await auditLogService.getSecurityLogs(cleanFilters());
  }

  renderLogsPage();
}

export async function renderAuditLogs() {
  await loadLogs();
}