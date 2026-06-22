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
    Low: "badge-info"
  };

  return `<span class="badge ${styles[level] || "badge-info"}">${level}</span>`;
}

function skeletonDashboard() {
  view.innerHTML = `
    <main class="dashboard-page">
      <div class="dashboard-header skeleton-box"></div>

      <section class="kpi-grid">
        ${Array.from({ length: 6 })
          .map(() => `<div class="dashboard-card skeleton-card"></div>`)
          .join("")}
      </section>

      <section class="dashboard-grid-3">
        <div class="dashboard-card skeleton-chart"></div>
        <div class="dashboard-card skeleton-chart"></div>
        <div class="dashboard-card skeleton-chart"></div>
      </section>
    </main>
  `;
}

function renderKpiCards(stats) {
  const cards = [
    {
      label: "Total Inventory Items",
      value: formatNumber(stats.total_items),
      icon: "📦",
      color: "blue"
    },
    {
      label: "Total Stock Value",
      value: formatCurrency(stats.total_value),
      icon: "💵",
      color: "green"
    },
    {
      label: "Low Stock Items",
      value: formatNumber(stats.low_stock),
      icon: "⚠️",
      color: "amber"
    },
    {
      label: "Stockout Risk (High)",
      value: formatNumber(stats.stockout_risk_high),
      icon: "🛡️",
      color: "red"
    },
    {
      label: "Active Alerts",
      value: formatNumber(stats.active_alerts),
      icon: "🔔",
      color: "amber"
    },
    {
      label: "Critical Items",
      value: formatNumber(stats.critical_items),
      icon: "✚",
      color: "blue"
    }
  ];

  return cards
    .map(
      card => `
        <article class="dashboard-card kpi-card">
          <div class="kpi-icon ${card.color}">
            ${card.icon}
          </div>

          <div>
            <p class="kpi-label">${card.label}</p>
            <h3 class="kpi-value">${card.value}</h3>
            <p class="kpi-trend success">↗ 12.5% from last week</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderRiskLegend(risk) {
  return `
    <div class="chart-legend">
      <div>
        <span class="legend-dot danger"></span>
        High Risk
        <strong>${risk.high.count} (${risk.high.percentage}%)</strong>
      </div>

      <div>
        <span class="legend-dot warning"></span>
        Medium Risk
        <strong>${risk.medium.count} (${risk.medium.percentage}%)</strong>
      </div>

      <div>
        <span class="legend-dot success"></span>
        Low Risk
        <strong>${risk.low.count} (${risk.low.percentage}%)</strong>
      </div>
    </div>
  `;
}

function renderTopRiskItems(items) {
  return items
    .slice(0, 5)
    .map(
      (item, index) => `
        <tr>
          <td>
            <strong>${index + 1}. ${item.name}</strong>
            <small>${item.category}</small>
          </td>

          <td>${badge(item.risk_level)}</td>

          <td>
            <span>${item.stockout_probability}</span>
            <div class="risk-bar">
              <span style="width:${item.stockout_probability * 100}%"></span>
            </div>
          </td>
        </tr>
      `
    )
    .join("");
}

function renderAlerts(alerts) {
  return alerts
    .slice(0, 4)
    .map(
      alert => `
        <div class="alert-row">
          <div class="alert-icon ${alert.severity.toLowerCase()}">⚠</div>

          <div>
            <strong>${alert.title}</strong>
            <p>${alert.description}</p>
          </div>

          ${badge(alert.severity)}
        </div>
      `
    )
    .join("");
}

function renderCategoryLegend(categories) {
  const colors = ["#6366F1", "#F59E0B", "#10B981", "#3B82F6", "#94A3B8"];

  return categories
    .map(
      (category, index) => `
        <div>
          <span style="background:${colors[index % colors.length]}"></span>
          ${category.name}
          <strong>${category.item_count} (${category.percentage}%)</strong>
        </div>
      `
    )
    .join("");
}

function renderPredictions(predictions) {
  return predictions
    .slice(0, 5)
    .map(
      item => `
        <tr>
          <td>${item.name}</td>
          <td>${item.facility}</td>
          <td>${item.predicted_date}</td>
          <td>${badge(item.risk_level)}</td>
        </tr>
      `
    )
    .join("");
}

function renderSystemStats(stats) {
  return `
    <article>
      <span>🏥</span>
      <h4>${stats.facilities}</h4>
      <p>Active Facilities</p>
    </article>

    <article>
      <span>🚚</span>
      <h4>${stats.vendors}</h4>
      <p>Active Vendors</p>
    </article>

    <article>
      <span>🏢</span>
      <h4>${stats.departments}</h4>
      <p>Active Departments</p>
    </article>

    <article>
      <span>👥</span>
      <h4>${stats.users}</h4>
      <p>System Users</p>
    </article>

    <article>
      <span>✅</span>
      <h4>System Status</h4>
      <p>${stats.system_status}</p>
    </article>
  `;
}

export async function renderDashboard() {
  destroyCharts();
  skeletonDashboard();

  const [
    stats,
    trend,
    risk,
    topRiskItems,
    alerts,
    categories,
    predictions,
    systemStats
  ] = await Promise.all([
    dashboardService.getInventoryStats(),
    dashboardService.getInventoryValueTrend("7d"),
    dashboardService.getStockoutRisk(),
    dashboardService.getTopRiskItems(),
    dashboardService.getAlerts(),
    dashboardService.getCategories(),
    dashboardService.getPredictions(),
    dashboardService.getSystemStats()
  ]);

  view.innerHTML = `
    <main class="dashboard-page">

      <section class="dashboard-title-row">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Overview of system performance and key metrics</p>
        </div>

        <button class="date-filter">
          📅 May 15 – May 21, 2025
        </button>
      </section>

      <section class="kpi-grid">
        ${renderKpiCards(stats)}
      </section>

      <section class="dashboard-grid-3 first-row">
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>Inventory Value Trend</h3>
            <select id="trendPeriod">
              <option value="7d">7 Days</option>
              <option value="30d">30 Days</option>
              <option value="3m">3 Months</option>
            </select>
          </div>

          <div class="chart-box">
            <canvas id="inventoryTrendChart"></canvas>
          </div>
        </article>

        <article class="dashboard-card">
          <div class="card-header">
            <h3>Stockout Risk Distribution</h3>
            <span>ⓘ</span>
          </div>

          <div class="chart-box small">
            <canvas id="riskChart"></canvas>
          </div>

          ${renderRiskLegend(risk)}
        </article>

        <article class="dashboard-card">
          <div class="card-header">
            <h3>Top 5 High Risk Items</h3>
            <a href="#">View All</a>
          </div>

          <table class="dashboard-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Risk Level</th>
                <th>Stockout Prob.</th>
              </tr>
            </thead>
            <tbody>
              ${renderTopRiskItems(topRiskItems)}
            </tbody>
          </table>
        </article>
      </section>

      <section class="dashboard-grid-3">
        <article class="dashboard-card">
          <div class="card-header">
            <h3>Alerts Summary</h3>
            <a href="#">View All</a>
          </div>

          ${renderAlerts(alerts)}
        </article>

        <article class="dashboard-card">
          <div class="card-header">
            <h3>Inventory by Category</h3>
          </div>

          <div class="category-layout">
            <div class="chart-box small">
              <canvas id="categoryChart"></canvas>
            </div>

            <div class="category-legend">
              ${renderCategoryLegend(categories)}
            </div>
          </div>
        </article>

        <article class="dashboard-card">
          <div class="card-header">
            <h3>Recent Predictions</h3>
            <a href="#">View All</a>
          </div>

          <table class="dashboard-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Facility</th>
                <th>Predicted Date</th>
                <th>Risk</th>
              </tr>
            </thead>

            <tbody>
              ${renderPredictions(predictions)}
            </tbody>
          </table>
        </article>
      </section>

      <section class="system-stats-row">
        ${renderSystemStats(systemStats)}
      </section>

    </main>
  `;

  createLineChart(
    "inventoryTrendChart",
    trend.labels,
    trend.values
  );

  createDoughnutChart(
    "riskChart",
    ["High Risk", "Medium Risk", "Low Risk"],
    [
      risk.high.count,
      risk.medium.count,
      risk.low.count
    ],
    ["#EF4444", "#F59E0B", "#10B981"]
  );

  createDoughnutChart(
    "categoryChart",
    categories.map(item => item.name),
    categories.map(item => item.item_count),
    ["#6366F1", "#F59E0B", "#10B981", "#3B82F6", "#94A3B8"]
  );

  document
    .getElementById("trendPeriod")
    .addEventListener("change", async event => {
      const newTrend =
        await dashboardService.getInventoryValueTrend(event.target.value);

      destroyCharts();

      createLineChart(
        "inventoryTrendChart",
        newTrend.labels,
        newTrend.values
      );

      createDoughnutChart(
        "riskChart",
        ["High Risk", "Medium Risk", "Low Risk"],
        [
          risk.high.count,
          risk.medium.count,
          risk.low.count
        ],
        ["#EF4444", "#F59E0B", "#10B981"]
      );

      createDoughnutChart(
        "categoryChart",
        categories.map(item => item.name),
        categories.map(item => item.item_count),
        ["#6366F1", "#F59E0B", "#10B981", "#3B82F6", "#94A3B8"]
      );
    });
}