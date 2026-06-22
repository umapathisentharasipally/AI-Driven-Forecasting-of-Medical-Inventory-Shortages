import { analyticsService } from "../../services/analytics.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import {
  destroyCharts,
  createLineChart,
  createBarChart,
  createDoughnutChart
} from "../../utils/chart-utils.js";

const view = document.getElementById("app");

let predictions = [];
let riskItems = [];
let riskSummary = null;
let activePeriod = "7d";

function skeletonForecasting() {
  view.innerHTML = `
    <main class="forecast-page">
      <div class="skeleton-box"></div>

      <section class="forecast-kpi-grid">
        <div class="forecast-card skeleton-card"></div>
        <div class="forecast-card skeleton-card"></div>
        <div class="forecast-card skeleton-card"></div>
        <div class="forecast-card skeleton-card"></div>
      </section>

      <section class="forecast-grid">
        <div class="forecast-card skeleton-chart"></div>
        <div class="forecast-card skeleton-chart"></div>
      </section>
    </main>
  `;
}

function number(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function percent(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function formatDate(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function riskBadge(level) {
  const map = {
    High: "badge-danger",
    Medium: "badge-warning",
    Low: "badge-success"
  };

  return `
    <span class="status-badge ${map[level] || "badge-muted"}">
      ${escapeHTML(level)}
    </span>
  `;
}

function renderHeader() {
  return `
    <section class="forecast-title-row">
      <div>
        <h1>Forecast & Trends</h1>
        <p>Analyze inventory demand, stockout risk, and prediction history.</p>
      </div>

      <select id="forecastPeriod" class="period-select">
        <option value="7d" ${activePeriod === "7d" ? "selected" : ""}>7 Days</option>
        <option value="30d" ${activePeriod === "30d" ? "selected" : ""}>30 Days</option>
        <option value="3m" ${activePeriod === "3m" ? "selected" : ""}>3 Months</option>
      </select>
    </section>
  `;
}

function renderKpis() {
  const high = riskSummary?.high?.count || 0;
  const medium = riskSummary?.medium?.count || 0;
  const low = riskSummary?.low?.count || 0;
  const total = riskSummary?.total || high + medium + low;

  return `
    <section class="forecast-kpi-grid">
      <article class="forecast-card kpi-mini">
        <span class="kpi-icon blue">🧠</span>
        <div>
          <p>Total Predictions</p>
          <h3>${number(predictions.length)}</h3>
        </div>
      </article>

      <article class="forecast-card kpi-mini">
        <span class="kpi-icon red">⚠️</span>
        <div>
          <p>High Risk Items</p>
          <h3>${number(high)}</h3>
        </div>
      </article>

      <article class="forecast-card kpi-mini">
        <span class="kpi-icon amber">📊</span>
        <div>
          <p>Medium Risk Items</p>
          <h3>${number(medium)}</h3>
        </div>
      </article>

      <article class="forecast-card kpi-mini">
        <span class="kpi-icon green">✅</span>
        <div>
          <p>Total Risk Records</p>
          <h3>${number(total || low)}</h3>
        </div>
      </article>
    </section>
  `;
}

function renderRiskLegend() {
  if (!riskSummary) return "";

  const rows = [
    {
      label: "High Risk",
      count: riskSummary.high?.count || 0,
      percentage: riskSummary.high?.percentage || 0,
      color: "danger"
    },
    {
      label: "Medium Risk",
      count: riskSummary.medium?.count || 0,
      percentage: riskSummary.medium?.percentage || 0,
      color: "warning"
    },
    {
      label: "Low Risk",
      count: riskSummary.low?.count || 0,
      percentage: riskSummary.low?.percentage || 0,
      color: "success"
    }
  ];

  return `
    <div class="forecast-legend">
      ${rows.map(row => `
        <div>
          <span class="legend-dot ${row.color}"></span>
          <p>${row.label}</p>
          <strong>${number(row.count)} (${percent(row.percentage)})</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function renderTopRiskTable() {
  return `
    <article class="forecast-card">
      <div class="card-header">
        <h2>Top High Risk Items</h2>
      </div>

      <div class="table-wrapper">
        <table class="forecast-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Item</th>
              <th>Category</th>
              <th>Risk</th>
              <th>Stockout Probability</th>
              <th>Stock</th>
            </tr>
          </thead>

          <tbody>
            ${
              riskItems.length
                ? riskItems.slice(0, 8).map((item, index) => `
                  <tr>
                    <td>${index + 1}</td>
                    <td><strong>${escapeHTML(item.name)}</strong></td>
                    <td>${escapeHTML(item.category)}</td>
                    <td>${riskBadge(item.risk_level)}</td>
                    <td>
                      <strong>${Number(item.stockout_probability || 0).toFixed(2)}</strong>
                      <div class="risk-progress">
                        <span style="width:${Number(item.stockout_probability || 0) * 100}%"></span>
                      </div>
                    </td>
                    <td>${number(item.current_stock)} / ${number(item.safety_stock)}</td>
                  </tr>
                `).join("")
                : `<tr><td colspan="6" class="empty-row">No high risk items found</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </article>
  `;
}

function renderPredictionsTable() {
  return `
    <article class="forecast-card">
      <div class="card-header">
        <h2>Recent Predictions</h2>
      </div>

      <div class="table-wrapper">
        <table class="forecast-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Item</th>
              <th>Facility</th>
              <th>Predicted Date</th>
              <th>Risk Level</th>
            </tr>
          </thead>

          <tbody>
            ${
              predictions.length
                ? predictions.slice(0, 10).map((item, index) => `
                  <tr>
                    <td>${index + 1}</td>
                    <td><strong>${escapeHTML(item.name)}</strong></td>
                    <td>${escapeHTML(item.facility || "-")}</td>
                    <td>${formatDate(item.predicted_date)}</td>
                    <td>${riskBadge(item.risk_level)}</td>
                  </tr>
                `).join("")
                : `<tr><td colspan="5" class="empty-row">No predictions found</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </article>
  `;
}

function renderForecastingPage() {
  view.innerHTML = `
    <main class="forecast-page">
      ${renderHeader()}
      ${renderKpis()}

      <section class="forecast-grid">
        <article class="forecast-card">
          <div class="card-header">
            <h2>Inventory Value Trend</h2>
          </div>
          <div class="chart-box">
            <canvas id="forecastTrendChart"></canvas>
          </div>
        </article>

        <article class="forecast-card">
          <div class="card-header">
            <h2>Stockout Risk Distribution</h2>
          </div>

          <div class="chart-box small">
            <canvas id="forecastRiskChart"></canvas>
          </div>

          ${renderRiskLegend()}
        </article>
      </section>

      <section class="forecast-grid">
        <article class="forecast-card">
          <div class="card-header">
            <h2>Risk Count Overview</h2>
          </div>
          <div class="chart-box">
            <canvas id="riskBarChart"></canvas>
          </div>
        </article>

        ${renderTopRiskTable()}
      </section>

      ${renderPredictionsTable()}
    </main>
  `;

  bindEvents();
}

async function drawCharts() {
  destroyCharts();

  const trend = await analyticsService.getInventoryValueTrend(activePeriod);

  createLineChart(
    "forecastTrendChart",
    trend.labels,
    trend.values,
    "Inventory Value"
  );

  createDoughnutChart(
    "forecastRiskChart",
    ["High Risk", "Medium Risk", "Low Risk"],
    [
      riskSummary.high?.count || 0,
      riskSummary.medium?.count || 0,
      riskSummary.low?.count || 0
    ],
    ["#EF4444", "#F59E0B", "#10B981"]
  );

  createBarChart(
    "riskBarChart",
    ["High", "Medium", "Low"],
    [
      riskSummary.high?.count || 0,
      riskSummary.medium?.count || 0,
      riskSummary.low?.count || 0
    ],
    "Risk Count"
  );
}

function bindEvents() {
  $("#forecastPeriod").addEventListener("change", async event => {
    activePeriod = event.target.value;
    await drawCharts();
  });
}

export async function renderForecasting() {
  skeletonForecasting();

  const [riskData, riskItemsData, predictionsData] = await Promise.all([
    analyticsService.getStockoutRisk(),
    analyticsService.getTopRiskItems(),
    analyticsService.getPredictions()
  ]);

  riskSummary = riskData;
  riskItems = riskItemsData;
  predictions = predictionsData;

  renderForecastingPage();

  await drawCharts();
}