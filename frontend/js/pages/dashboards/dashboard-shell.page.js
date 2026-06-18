export function DashboardShellPage() {
  return `
    <section class="page-content">
      <div class="stat-grid">
        ${statCard("Total Shipments", "24", "↑ 12% this month", "📦", "blue")}
        ${statCard("In Transit", "16", "↑ 8% this month", "🚚", "green")}
        ${statCard("Delivered", "7", "↑ 14% this month", "✓", "purple")}
        ${statCard("Delayed", "3", "↓ 5% this month", "⏱", "orange")}
        ${statCard("Alerts", "5", "View all alerts", "⚠", "red")}
      </div>

      <div class="dashboard-grid">
        <div class="card dashboard-card">
          <div class="card-header">
            <h2>Shipments Overview</h2>
            <button class="badge blue">This Month</button>
          </div>
          <div class="fake-line-chart"></div>
        </div>

        <div class="card dashboard-card">
          <h2>Shipment Status Distribution</h2>
          <div class="map-placeholder"></div>
        </div>

        <div class="card dashboard-card">
          <div class="card-header">
            <h2>Live Shipment Map</h2>
            <button class="badge blue">View Full Map</button>
          </div>
          <div class="map-placeholder"></div>
        </div>
      </div>

      <div class="dashboard-bottom">
        <div class="card dashboard-card">
          <div class="card-header">
            <h2>Recent Shipments</h2>
            <button class="badge blue">View All</button>
          </div>

          ${shipmentRow("SHIP-2025-00024", "Delhi → Mumbai", "In Transit", "blue")}
          ${shipmentRow("SHIP-2025-00023", "Bangalore → Hyderabad", "Delivered", "green")}
          ${shipmentRow("SHIP-2025-00022", "Chennai → Pune", "In Transit", "blue")}
          ${shipmentRow("SHIP-2025-00021", "Kolkata → Delhi", "Delayed", "orange")}
        </div>

        <div class="card dashboard-card">
          <div class="card-header">
            <h2>Active Devices</h2>
            <button class="badge blue">View All</button>
          </div>

          ${deviceRow("Device-1001", "Online")}
          ${deviceRow("Device-1002", "Online")}
          ${deviceRow("Device-1003", "Online")}
          ${deviceRow("Device-1004", "Offline")}
        </div>

        <div class="card dashboard-card">
          <div class="card-header">
            <h2>Recent Alerts</h2>
            <button class="badge blue">View All</button>
          </div>

          ${alertRow("High Temperature", "Device-1004: Temperature is above 30°C")}
          ${alertRow("Low Battery", "Device-1002: Battery level below 20%")}
          ${alertRow("Signal Lost", "Device-1005: Signal lost")}
          ${alertRow("High Humidity", "Device-1003: Humidity is above 70%")}
        </div>
      </div>
    </section>
  `;
}

function statCard(title, value, change, icon, color) {
  return `
    <div class="card stat-card">
      <div>
        <div class="stat-title">${title}</div>
        <div class="stat-value">${value}</div>
        <div class="stat-change">${change}</div>
      </div>
      <div class="stat-icon ${color}">${icon}</div>
    </div>
  `;
}

function shipmentRow(id, route, status, color) {
  return `
    <div class="list-row">
      <div>
        <strong>${id}</strong>
        <p>${route}</p>
      </div>
      <span class="badge ${color}">${status}</span>
    </div>
  `;
}

function deviceRow(device, status) {
  return `
    <div class="list-row">
      <div>
        <strong>${device}</strong>
        <p>Shipment connected</p>
      </div>
      <span style="color:${status === "Online" ? "#22c55e" : "#ef4444"};font-weight:800">
        ${status}
      </span>
    </div>
  `;
}

function alertRow(title, message) {
  return `
    <div class="list-row">
      <div>
        <strong>${title}</strong>
        <p>${message}</p>
      </div>
    </div>
  `;
}