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
    Low: "badge-info"
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
      label: "Inventory Items",
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
      label: "Active Vendors",
      value: formatNumber(stats.vendors),
      icon: "🚚",
      color: "purple"
    },
    {
      label: "Pending POs",
      value: formatNumber(stats.pending_orders || 0),
      icon: "📋",
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
            <p class="kpi-trend success">↗ 8.2% from last month</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderStockStatus(items) {
  return items
    .slice(0, 8)
    .map(
      (item, index) => `
        <tr>
          <td><strong>${index + 1}. ${item.name}</strong></td>
          <td>${item.current_stock}</td>
          <td>${item.min_threshold}</td>
          <td>${item.max_threshold}</td>
          <td>${badge(item.stock_status)}</td>
        </tr>
      `
    )
    .join("");
}

function renderVendorPerformance(vendors) {
  return vendors
    .slice(0, 6)
    .map(
      vendor => `
        <tr>
          <td><strong>${vendor.name}</strong></td>
          <td>${vendor.orders_count}</td>
          <td>${formatNumber(vendor.total_value)}</td>
          <td>${vendor.delivery_rate}%</td>
          <td>${badge(vendor.performance_rating)}</td>
        </tr>
      `
    )
    .join("");
}

function renderPurchaseOrders(orders) {
  const statusColors = {
    pending: "warning",
    confirmed: "info",
    shipped: "primary",
    delivered: "success",
    cancelled: "danger"
  };

  return orders
    .slice(0, 6)
    .map(
      order => `
        <tr>
          <td><strong>${order.po_number}</strong></td>
          <td>${order.vendor}</td>
          <td>${formatCurrency(order.amount)}</td>
          <td>${order.expected_date}</td>
          <td><span class="badge badge-${statusColors[order.status] || "info"}">${order.status}</span></td>
        </tr>
      `
    )
    .join("");
}

function renderReorderPoints(items) {
  return items
    .slice(0, 5)
    .map(
      item => `
        <tr>
          <td>${item.name}</td>
          <td>${item.current_stock}</td>
          <td>${item.reorder_point}</td>
          <td>${item.lead_time_days} days</td>
          <td>${formatCurrency(item.unit_cost)}</td>
        </tr>
      `
    )
    .join("");
}

export async function renderSupplyManagerDashboard() {
  destroyCharts();
  skeletonDashboard();

  const [
    stats,
    stockStatus,
    vendorPerformance,
    purchaseOrders,
    inventoryTrend,
    categoryDistribution,
    reorderPoints,
    lowStockAlerts
  ] = await Promise.all([
    dashboardService.getInventoryStats(),
    dashboardService.getStockStatus?.() || Promise.resolve([]),
    dashboardService.getVendorPerformance?.() || Promise.resolve([]),
    dashboardService.getPurchaseOrders?.() || Promise.resolve([]),
    dashboardService.getInventoryValueTrend("30d"),
    dashboardService.getCategories(),
    dashboardService.getReorderPoints?.() || Promise.resolve([]),
    dashboardService.getAlerts()
  ]);

  view.innerHTML = `
    <main class="dashboard-page supply-manager-dashboard">

      <section class="dashboard-title-row">
        <div>
          <h1>📦 Supply Manager Dashboard</h1>
          <p>Inventory & Vendor Management Hub</p>
        </div>
        <div class="dashboard-actions">
          <button id="createPoBtn" class="primary-btn">
            ➕ Create Purchase Order
          </button>
          <button id="runInventoryCheckBtn" class="secondary-btn">
            🔍 Run Inventory Check
          </button>
        </div>
      </section>

      <!-- KPI Cards -->
      <section class="kpi-grid">
        ${renderKpiCards(stats)}
      </section>

      <!-- Main Grid -->
      <section class="dashboard-grid-3 first-row">
        <!-- Stock Status -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📊 Stock Status Overview</h3>
            <a href="#inventory" class="view-all">View All →</a>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Current</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${renderStockStatus(stockStatus)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- Inventory Value Trend -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📈 Inventory Value Trend</h3>
            <span class="period-label">Last 30 Days</span>
          </div>
          <canvas id="inventoryTrendChart" style="max-height: 300px;"></canvas>
        </article>

        <!-- Category Distribution -->
        <article class="dashboard-card">
          <div class="card-header">
            <h3>📂 Item Distribution by Category</h3>
          </div>
          <canvas id="categoryDistributionChart" style="max-height: 300px;"></canvas>
          <div class="chart-legend category-legend">
            ${categoryDistribution
              .map(
                cat => `
              <div>
                <span class="legend-dot"></span>
                ${cat.name}: <strong>${cat.item_count} items</strong>
              </div>
            `
              )
              .join("")}
          </div>
        </article>
      </section>

      <!-- Second Row -->
      <section class="dashboard-grid-2">
        <!-- Vendor Performance -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>🚚 Vendor Performance</h3>
            <a href="#vendors" class="view-all">View All →</a>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Orders</th>
                  <th>Total Value</th>
                  <th>On-Time %</th>
                  <th>Rating</th>
                </tr>
              </thead>
              <tbody>
                ${renderVendorPerformance(vendorPerformance)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- Recent Purchase Orders -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>📋 Recent Purchase Orders</h3>
            <a href="#purchase-orders" class="view-all">View All →</a>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>PO#</th>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Expected Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${renderPurchaseOrders(purchaseOrders)}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <!-- Third Row -->
      <section class="dashboard-grid-2">
        <!-- Reorder Points -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>🔔 Items Near Reorder Point</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Current Stock</th>
                  <th>Reorder Point</th>
                  <th>Lead Time</th>
                  <th>Unit Cost</th>
                </tr>
              </thead>
              <tbody>
                ${renderReorderPoints(reorderPoints)}
              </tbody>
            </table>
          </div>
        </article>

        <!-- Low Stock Alerts -->
        <article class="dashboard-card large-card">
          <div class="card-header">
            <h3>⚠️ Active Alerts</h3>
            <span class="alert-count">${lowStockAlerts.length}</span>
          </div>
          <div class="alerts-list">
            ${lowStockAlerts
              .slice(0, 5)
              .map(
                alert => `
              <div class="alert-row alert-${alert.severity.toLowerCase()}">
                <div class="alert-icon">⚠️</div>
                <div>
                  <strong>${alert.title}</strong>
                  <p>${alert.description}</p>
                  <small>${alert.timestamp}</small>
                </div>
              </div>
            `
              )
              .join("")}
          </div>
        </article>
      </section>

    </main>
  `;

  // Initialize Charts
  createLineChart("inventoryTrendChart", {
    labels: inventoryTrend.labels || [],
    datasets: [{
      label: "Inventory Value",
      data: inventoryTrend.values || [],
      borderColor: "#10B981",
      backgroundColor: "rgba(16, 185, 129, 0.1)",
      tension: 0.4
    }]
  });

  createDoughnutChart("categoryDistributionChart", {
    labels: categoryDistribution.map(c => c.name),
    datasets: [{
      data: categoryDistribution.map(c => c.item_count),
      backgroundColor: ["#6366F1", "#F59E0B", "#10B981", "#3B82F6", "#94A3B8"]
    }]
  });

  // Add event listeners
  document.getElementById("createPoBtn")?.addEventListener("click", () => {
    window.navigateTo("purchase-orders");
  });

  document.getElementById("runInventoryCheckBtn")?.addEventListener("click", () => {
    alert("Running inventory check...");
  });
}
