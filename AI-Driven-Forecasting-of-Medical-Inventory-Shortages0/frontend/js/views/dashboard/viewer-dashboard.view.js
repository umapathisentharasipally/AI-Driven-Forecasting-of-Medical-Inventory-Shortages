import { dashboardService } from "../../services/dashboard.service.js";
import {
  destroyCharts,
  createLineChart,
  createDoughnutChart
} from "../../utils/chart-utils.js";

const view = document.getElementById("app");

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatCurrency(value) {
  if (value >= 1000000) {
    return `$ ${(value / 1000000).toFixed(2)}M`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(value);
}

function badge(level) {
  const styles = {
    High: "badge-danger",
    Medium: "badge-warning",
    Low: "badge-info",
    Critical: "badge-danger",
    Normal: "badge-success"
  };
  return `<span class="badge ${styles[level] || "badge-info"}">${level}</span>`;
}

function skeletonDashboard() {
  view.innerHTML = `
    <main class="dashboard-page">
      <div class="dashboard-header skeleton-box"></div>
      <section class="kpi-grid">
        ${Array.from({ length: 4 })
          .map(() => `<div class="dashboard-card skeleton-card"></div>`)
          .join("")}
      </section>
      <section class="dashboard-grid-2">
        <div class="dashboard-card skeleton-chart"></div>
        <div class="dashboard-card skeleton-chart"></div>
      </section>
    </main>
  `;
}

function renderKpiCards(stats) {
  const cards = [
    {
      label: "Total Items",
      value: formatNumber(stats.total_items),
      icon: "📦",
      color: "blue"
    },
    {
      label: "Total Value",
      value: formatCurrency(stats.total_value),
      icon: "💰",
      color: "green"
    },
    {
      label: "Low Stock Items",
      value: formatNumber(stats.low_stock),
      icon: "⚠️",
      color: "amber"
    },
    {
      label: "Active Alerts",
      value: formatNumber(stats.active_alerts),
      icon: "🔔",
      color: "red"
    }
  ];

  return cards
    .map(
      card => `
        <article class="dashboard-card kpi-card read-only">
          <div class="kpi-icon ${card.color}">
            ${card.icon}
          </div>
          <div>
            <p class="kpi-label">${card.label}</p>
            <h3 class="kpi-value">${card.value}</h3>
          </div>
        </article>
      `
    )
    .join("");
}

function renderTopItems(items) {
  return items
    .slice(0, 6)
    .map(
      (item, index) => `
        <tr>
          <td><strong>${index + 1}. ${item.name}</strong></td>
          <td>${item.category}</td>
          <td>${formatNumber(item.current_stock)}</td>
          <td>${badge(item.status)}</td>
        </tr>
      `
    )
    .join("");
}

function renderRecentAlerts(alerts) {
  return alerts
    .slice(0, 5)
    .map(
      alert => `
        <div class="alert-row alert-${alert.severity.toLowerCase()}">
          <div class="alert-icon">
            ${alert.severity === "High" ? "🔴" : alert.severity === "Medium" ? "🟡" : "🟢"}
          </div>
          <div class="alert-content">
            <strong>${alert.title}</strong>
            <p>${alert.description}</p>
            <small>${alert.timestamp}</small>
          </div>
          <div class="alert-badge">
            ${badge(alert.severity)}
          </div>
        </div>
      `
    )
    .join("");
}

function renderInventoryHealth(stats) {
  const healthPercentage = ((stats.total_items - stats.low_stock) / stats.total_items * 100).toFixed(1);
  const healthStatus = healthPercentage >= 80 ? "Healthy" : healthPercentage >= 60 ? "Good" : "At Risk";
  const healthColor = healthPercentage >= 80 ? "success" : healthPercentage >= 60 ? "warning" : "danger";

  return `
    <div class="health-card">
      <div class="health-status ${healthColor}">
        <div class="health-circle">
          <svg viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="${healthPercentage * 2.83} 283" />
          </svg>
          <div class="health-text">
            <span class="health-percentage">${healthPercentage}%</span>
            <span class="health-label">${healthStatus}</span>
          </div>
        </div>
        <div class="health-details">
          <p><strong>✓ Items in Stock:</strong> ${formatNumber(stats.total_items - stats.low_stock)}</p>
          <p><strong>⚠️ Low Stock:</strong> ${formatNumber(stats.low_stock)}</p>
          <p><strong>Last Updated:</strong> Just now</p>
        </div>
      </div>
    </div>
  `;
}

function renderCategoryOverview(categories) {
  const colors = ["#6366F1", "#F59E0B", "#10B981", "#3B82F6", "#EC4899"];
  return `
    <div class="category-list">
      ${categories
        .slice(0, 5)
        .map(
          (cat, index) => `
        <div class="category-item">
          <div class="category-indicator" style="background-color: ${colors[index % colors.length]}"></div>
          <div class="category-info">
            <strong>${cat.name}</strong>
            <small>${cat.item_count} items</small>
          </div>
          <div class="category-value">${cat.item_count}</div>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

export async function renderViewerDashboard() {
  destroyCharts();
  skeletonDashboard();

  const [
    stats,
    topItems,
    alerts,
    categories,
    trendData,
    riskDistribution
  ] = await Promise.all([
    dashboardService.getInventoryStats(),
    dashboardService.getTopRiskItems?.() || Promise.resolve([]),
    dashboardService.getAlerts(),
    dashboardService.getCategories(),
    dashboardService.getInventoryValueTrend("7d"),
    dashboardService.getStockoutRisk()
  ]);

  view.innerHTML = `
    <main class="dashboard-page viewer-dashboard">

      <section class="dashboard-title-row">
        <div>
          <h1>👁️ Inventory Overview</h1>
          <p>Read-only view of current inventory status</p>
        </div>
        <div class="dashboard-actions">
          <button id="refreshBtn" class="secondary-btn">
            🔄 Refresh
          </button>
        </div>
      </section>

      <!-- KPI Cards -->
      <section class="kpi-grid">
        ${renderKpiCards(stats)}
      </section>

      <!-- Main Grid -->
      <section class="dashboard-grid-2 first-row">
        <!-- Inventory Health -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>📊 Inventory Health</h3>
          </div>
          ${renderInventoryHealth(stats)}
        </article>

        <!-- Weekly Trend -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>📈 7-Day Value Trend</h3>
          </div>
          <canvas id="trendChart" style="max-height: 250px;"></canvas>
        </article>
      </section>

      <!-- Second Row -->
      <section class="dashboard-grid-2">
        <!-- Top Items -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📦 Top Inventory Items</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item Name</th>
                  <th>Category</th>
                  <th>Current Stock</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${renderTopItems(topItems)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- Category Distribution -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📂 Categories Overview</h3>
          </div>
          ${renderCategoryOverview(categories)}
        </article>
      </section>

      <!-- Third Row -->
      <section class="dashboard-grid-2">
        <!-- Risk Distribution -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>⚖️ Inventory Risk Levels</h3>
          </div>
          <canvas id="riskChart" style="max-height: 300px;"></canvas>
          <div class="chart-legend compact">
            <div><span class="legend-dot danger"></span> High: ${riskDistribution.high?.count || 0}</div>
            <div><span class="legend-dot warning"></span> Medium: ${riskDistribution.medium?.count || 0}</div>
            <div><span class="legend-dot success"></span> Low: ${riskDistribution.low?.count || 0}</div>
          </div>
        </article>

        <!-- Recent Alerts -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>🔔 Recent Alerts</h3>
            <span class="alert-badge">${alerts.length}</span>
          </div>
          <div class="alerts-list">
            ${alerts.length > 0 
              ? renderRecentAlerts(alerts)
              : '<div class="no-data"><p>✓ No active alerts</p></div>'
            }
          </div>
        </article>
      </section>

      <!-- Footer Info -->
      <section class="dashboard-footer">
        <div class="footer-info">
          <small>📍 You are viewing data in read-only mode</small>
          <small>🔄 Last updated: Just now</small>
          <small>👤 Role: Viewer</small>
        </div>
      </section>

    </main>
  `;

  // Initialize Charts
  createLineChart("trendChart", {
    labels: trendData.labels || [],
    datasets: [{
      label: "Inventory Value",
      data: trendData.values || [],
      borderColor: "#3B82F6",
      backgroundColor: "rgba(59, 130, 246, 0.1)",
      tension: 0.4,
      fill: true
    }]
  });

  createDoughnutChart("riskChart", {
    labels: ["High Risk", "Medium Risk", "Low Risk"],
    datasets: [{
      data: [
        riskDistribution.high?.count || 0,
        riskDistribution.medium?.count || 0,
        riskDistribution.low?.count || 0
      ],
      backgroundColor: ["#EF4444", "#FBBF24", "#10B981"]
    }]
  });

  // Add event listeners
  document.getElementById("refreshBtn")?.addEventListener("click", () => {
    location.reload();
  });
}
