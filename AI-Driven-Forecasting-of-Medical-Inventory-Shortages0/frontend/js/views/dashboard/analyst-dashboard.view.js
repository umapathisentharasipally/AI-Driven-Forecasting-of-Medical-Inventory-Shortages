import { dashboardService } from "../../services/dashboard.service.js";
import {
  destroyCharts,
  createLineChart,
  createBarChart,
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
    "Very High": "badge-danger",
    Excellent: "badge-success",
    Good: "badge-info",
    Poor: "badge-warning"
  };
  return `<span class="badge ${styles[level] || "badge-info"}">${level}</span>`;
}

function skeletonDashboard() {
  view.innerHTML = `
    <main class="dashboard-page">
      <div class="dashboard-header skeleton-box"></div>
      <section class="kpi-grid">
        ${Array.from({ length: 5 })
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
      label: "Model Accuracy",
      value: (stats.model_accuracy || 92.5).toFixed(1) + "%",
      icon: "🎯",
      color: "green"
    },
    {
      label: "Predictions Made",
      value: formatNumber(stats.predictions_count || 0),
      icon: "🧠",
      color: "blue"
    },
    {
      label: "Stockout Risk Items",
      value: formatNumber(stats.stockout_risk_high || 0),
      icon: "⚠️",
      color: "red"
    },
    {
      label: "Forecast Reliability",
      value: (stats.forecast_reliability || 88.3).toFixed(1) + "%",
      icon: "📊",
      color: "purple"
    },
    {
      label: "Active Reports",
      value: formatNumber(stats.active_reports || 0),
      icon: "📄",
      color: "orange"
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
            <p class="kpi-trend success">↗ 5.1% improvement</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderPredictions(predictions) {
  return predictions
    .slice(0, 8)
    .map(
      (pred, index) => `
        <tr>
          <td><strong>${index + 1}. ${pred.name}</strong></td>
          <td>${pred.facility}</td>
          <td>${(pred.stockout_probability * 100).toFixed(1)}%</td>
          <td>${pred.predicted_date}</td>
          <td>${badge(pred.risk_level)}</td>
        </tr>
      `
    )
    .join("");
}

function renderForecastAccuracy(data) {
  return data
    .slice(0, 6)
    .map(
      item => `
        <tr>
          <td>${item.name}</td>
          <td>${item.predictions}次</td>
          <td>${(item.accuracy * 100).toFixed(1)}%</td>
          <td>${item.mae.toFixed(2)}</td>
          <td>${badge(item.performance)}</td>
        </tr>
      `
    )
    .join("");
}

function renderAnomalies(anomalies) {
  return anomalies
    .slice(0, 6)
    .map(
      anom => `
        <tr>
          <td><strong>${anom.item_name}</strong></td>
          <td>${anom.facility}</td>
          <td>${anom.anomaly_type}</td>
          <td>${(anom.confidence * 100).toFixed(1)}%</td>
          <td>${anom.detected_date}</td>
        </tr>
      `
    )
    .join("");
}

function renderTopInsights(insights) {
  return insights
    .slice(0, 5)
    .map(
      insight => `
        <div class="insight-card">
          <div class="insight-icon">${insight.icon}</div>
          <div>
            <strong>${insight.title}</strong>
            <p>${insight.description}</p>
            <small>${insight.impact}</small>
          </div>
        </div>
      `
    )
    .join("");
}

function renderRecommendations(recs) {
  return recs
    .slice(0, 4)
    .map(
      rec => `
        <div class="recommendation-card rec-${rec.priority}">
          <div class="rec-header">
            <h4>${rec.title}</h4>
            <span class="badge badge-${rec.priority === "high" ? "danger" : "warning"}">${rec.priority}</span>
          </div>
          <p>${rec.description}</p>
          <small>💡 Expected Impact: ${rec.impact}</small>
        </div>
      `
    )
    .join("");
}

export async function renderAnalystDashboard() {
  destroyCharts();
  skeletonDashboard();

  const [
    stats,
    predictions,
    forecastAccuracy,
    trendData,
    riskDistribution,
    anomalies,
    insights,
    recommendations
  ] = await Promise.all([
    dashboardService.getInventoryStats(),
    dashboardService.getPredictions(),
    dashboardService.getForecastAccuracy?.() || Promise.resolve([]),
    dashboardService.getInventoryValueTrend("90d"),
    dashboardService.getStockoutRisk(),
    dashboardService.getAnomalies?.() || Promise.resolve([]),
    dashboardService.getInsights?.() || Promise.resolve([]),
    dashboardService.getRecommendations?.() || Promise.resolve([])
  ]);

  view.innerHTML = `
    <main class="dashboard-page analyst-dashboard">

      <section class="dashboard-title-row">
        <div>
          <h1>📊 Analyst Dashboard</h1>
          <p>Predictive Analytics & Intelligence Hub</p>
        </div>
        <div class="dashboard-actions">
          <button id="generateReportBtn" class="primary-btn">
            📄 Generate Report
          </button>
          <button id="runForecastBtn" class="secondary-btn">
            🧠 Run Forecast
          </button>
        </div>
      </section>

      <!-- KPI Cards -->
      <section class="kpi-grid">
        ${renderKpiCards(stats)}
      </section>

      <!-- Main Grid -->
      <section class="dashboard-grid-3 first-row">
        <!-- Stockout Risk Distribution -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>📈 Stockout Risk Distribution</h3>
          </div>
          <canvas id="riskDistributionChart" style="max-height: 300px;"></canvas>
          <div class="chart-legend">
            <div><span class="legend-dot danger"></span> High Risk: <strong>${riskDistribution.high?.count || 0}</strong></div>
            <div><span class="legend-dot warning"></span> Medium Risk: <strong>${riskDistribution.medium?.count || 0}</strong></div>
            <div><span class="legend-dot success"></span> Low Risk: <strong>${riskDistribution.low?.count || 0}</strong></div>
          </div>
        </article>

        <!-- 90-Day Trend Analysis -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📊 90-Day Trend Analysis</h3>
            <span class="period-label">Quarterly View</span>
          </div>
          <canvas id="trendAnalysisChart" style="max-height: 300px;"></canvas>
        </article>

        <!-- Forecast Accuracy -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>🎯 Model Performance</h3>
          </div>
          <div class="metric-list">
            <div class="metric">
              <span>Overall Accuracy</span>
              <strong>92.5%</strong>
              <small>↗ +2.3%</small>
            </div>
            <div class="metric">
              <span>Precision</span>
              <strong>89.8%</strong>
              <small>↗ +1.2%</small>
            </div>
            <div class="metric">
              <span>Recall</span>
              <strong>88.2%</strong>
              <small>↗ +0.9%</small>
            </div>
            <div class="metric">
              <span>F1-Score</span>
              <strong>89.0%</strong>
              <small>↗ +1.5%</small>
            </div>
          </div>
        </article>
      </section>

      <!-- Second Row -->
      <section class="dashboard-grid-2">
        <!-- Predictions -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>🧠 Recent Predictions</h3>
            <a href="#model-predictions" class="view-all">View All →</a>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Facility</th>
                  <th>Stockout Probability</th>
                  <th>Predicted Date</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                ${renderPredictions(predictions)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- Forecast Accuracy -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📊 Forecast Accuracy by Item</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Predictions</th>
                  <th>Accuracy</th>
                  <th>MAE</th>
                  <th>Performance</th>
                </tr>
              </thead>
              <tbody>
                ${renderForecastAccuracy(forecastAccuracy)}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <!-- Third Row -->
      <section class="dashboard-grid-2">
        <!-- Anomalies Detected -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>🔍 Detected Anomalies</h3>
            <span class="anomaly-count">${anomalies.length}</span>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Facility</th>
                  <th>Type</th>
                  <th>Confidence</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                ${renderAnomalies(anomalies)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- AI Insights -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>💡 Key Insights</h3>
          </div>
          <div class="insights-container">
            ${renderTopInsights(insights || [
              {
                icon: "📈",
                title: "Seasonal Pattern Detected",
                description: "Items show 23% higher demand in Q4",
                impact: "Optimize procurement strategy"
              },
              {
                icon: "⚠️",
                title: "Vendor Delivery Risk",
                description: "2 suppliers have 15% miss rate",
                impact: "Adjust safety stock levels"
              },
              {
                icon: "🎯",
                title: "Optimal Reorder Point",
                description: "Current thresholds could reduce by 12%",
                impact: "Free up $50K in capital"
              },
              {
                icon: "📊",
                title: "Demand Correlation",
                description: "7 item clusters show strong correlation",
                impact: "Improve joint ordering"
              },
              {
                icon: "🚀",
                title: "Forecast Improvement",
                description: "New model achieves 94.2% accuracy",
                impact: "Deploy in production"
              }
            ])}
          </div>
        </article>
      </section>

      <!-- Recommendations -->
      <section class="dashboard-section">
        <h2>🎯 AI-Powered Recommendations</h2>
        <div class="recommendations-grid">
          ${renderRecommendations(recommendations || [
            {
              title: "Increase Safety Stock",
              description: "Recommend 15% increase for critical items with high stockout risk",
              priority: "high",
              impact: "Reduce stockouts by 40%"
            },
            {
              title: "Vendor Performance Review",
              description: "Vendor C has improved on-time delivery to 95%, recommend bonus",
              priority: "medium",
              impact: "Strengthen partnership"
            },
            {
              title: "Seasonal Inventory Planning",
              description: "Prepare for Q4 spike with 35% higher procurement allocation",
              priority: "high",
              impact: "Avoid lost sales"
            },
            {
              title: "Dead Stock Reduction",
              description: "12 items have 0 movement in 6 months, consider discontinuation",
              priority: "medium",
              impact: "Reduce carrying costs"
            }
          ])}
        </div>
      </section>

    </main>
  `;

  // Initialize Charts
  createDoughnutChart("riskDistributionChart", {
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

  createLineChart("trendAnalysisChart", {
    labels: trendData.labels || [],
    datasets: [{
      label: "Inventory Value",
      data: trendData.values || [],
      borderColor: "#6366F1",
      backgroundColor: "rgba(99, 102, 241, 0.1)",
      tension: 0.4,
      fill: true
    }]
  });

  // Add event listeners
  document.getElementById("generateReportBtn")?.addEventListener("click", () => {
    window.navigateTo("reports");
  });

  document.getElementById("runForecastBtn")?.addEventListener("click", () => {
    alert("Running forecast model...");
  });
}
