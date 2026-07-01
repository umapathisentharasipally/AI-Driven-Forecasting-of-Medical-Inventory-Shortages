# Role-Based Dashboards Implementation

## Overview
This project now features 4 role-specific dashboards tailored to different user needs:

1. **Admin Dashboard** - Full system control and oversight
2. **Supply Manager Dashboard** - Inventory and vendor management
3. **Analyst Dashboard** - Predictive analytics and insights
4. **Viewer Dashboard** - Read-only inventory overview

---

## Dashboard Architecture

### Routing System
The dashboard router automatically detects the user's role and displays the appropriate dashboard.

**File:** `frontend/js/views/dashboard/dashboard.view.js`

```javascript
export async function renderDashboard() {
  // Gets user role from localStorage
  const userRole = JSON.parse(localStorage.getItem("user")).role;
  
  // Routes to appropriate dashboard
  switch (userRole?.toLowerCase()) {
    case "admin": return renderAdminDashboard();
    case "supply_manager": return renderSupplyManagerDashboard();
    case "analyst": return renderAnalystDashboard();
    case "viewer": return renderViewerDashboard();
  }
}
```

---

## Dashboard Details

### 1. **Admin Dashboard** (👨‍💼)
**Role:** `admin`  
**Permission:** `admin:all`

#### Purpose
Complete system oversight and control. Access to all features and metrics.

#### Key Components
- **KPI Cards (6):** Total Items, Stock Value, Low Stock, Stockout Risk, Active Alerts, Critical Items
- **Inventory Trend Chart:** 7/30/90 day history with period selector
- **Risk Distribution:** Doughnut chart showing high/medium/low risk items
- **Top Risk Items:** Table of 5 highest risk items with stockout probability
- **Alerts Summary:** Latest system alerts with severity levels
- **Category Distribution:** Inventory breakdown by category
- **Predictions:** Recent ML predictions for stockouts
- **System Stats:** Active facilities, vendors, departments, users, system status
- **ML Controls:** Run batch predictions button

#### Features
- Period switching (7d, 30d, 3m) for trend analysis
- Run ML predictions on-demand
- Complete audit trail visibility
- System performance metrics

#### File Location
- Main Router: `frontend/js/views/dashboard/dashboard.view.js`

---

### 2. **Supply Manager Dashboard** (📦)
**Role:** `supply_manager`  
**Permission:** `inventory:*`, `vendors:*`, `alerts:read`, `reports:read`

#### Purpose
Focused on inventory operations, vendor management, and procurement.

#### Key Components
- **KPI Cards (5):** Inventory Items, Stock Value, Low Stock, Active Vendors, Pending POs
- **Stock Status:** Table showing current, min, and max stock levels
- **Inventory Value Trend:** 30-day trend visualization
- **Category Distribution:** Doughnut chart of item breakdown
- **Vendor Performance:** Table with delivery rates and ratings
- **Purchase Orders:** Recent PO tracking with status
- **Reorder Points:** Items near reorder threshold
- **Active Alerts:** Low stock and inventory-related warnings

#### Features
- Create new purchase orders
- Run inventory checks
- Track vendor performance metrics
- Monitor reorder points
- Quick access to inventory management pages

#### File Location
`frontend/js/views/dashboard/supply-manager-dashboard.view.js`

---

### 3. **Analyst Dashboard** (📊)
**Role:** `analyst`  
**Permission:** `forecasting:*`, `reports:*`, `alerts:read`

#### Purpose
Predictive analytics, forecasting, and data-driven insights.

#### Key Components
- **KPI Cards (5):** Model Accuracy, Predictions Made, Stockout Risk Items, Forecast Reliability, Active Reports
- **Risk Distribution:** Doughnut chart of stockout risk levels
- **90-Day Trend Analysis:** Quarterly inventory value trends
- **Model Performance Metrics:**
  - Overall Accuracy: 92.5%
  - Precision: 89.8%
  - Recall: 88.2%
  - F1-Score: 89.0%
- **Recent Predictions:** Table with stockout probabilities
- **Forecast Accuracy by Item:** Model performance breakdown
- **Detected Anomalies:** Unusual patterns in inventory data
- **Key Insights:** AI-generated business insights
- **AI Recommendations:** Priority-based actionable recommendations

#### Features
- Generate detailed reports
- Run forecast models
- Analyze anomalies
- View AI-powered insights
- Get priority recommendations

#### File Location
`frontend/js/views/dashboard/analyst-dashboard.view.js`

---

### 4. **Viewer Dashboard** (👁️)
**Role:** `viewer`  
**Permission:** Read-only access to inventory, vendors, predictions, alerts, reports

#### Purpose
Read-only overview for stakeholders who need visibility but no editing rights.

#### Key Components
- **KPI Cards (4):** Total Items, Total Value, Low Stock Items, Active Alerts
- **Inventory Health:** Circular health indicator (0-100%)
  - Shows healthy/good/at-risk status
  - Breakdown of in-stock vs. low-stock items
- **7-Day Trend:** Value trend over the past week
- **Top Inventory Items:** Top 6 items by value
- **Categories Overview:** Item distribution by category
- **Inventory Risk Levels:** Risk distribution chart
- **Recent Alerts:** Latest system alerts (max 5)
- **Footer Info:** Read-only mode indicator, last updated timestamp

#### Features
- Real-time refresh button
- Simplified, clean interface
- Health status visualization
- No data modification capabilities

#### File Location
`frontend/js/views/dashboard/viewer-dashboard.view.js`

---

## User Roles & Permissions Matrix

| Role | Admin | Supply Manager | Analyst | Viewer |
|------|:-----:|:--------------:|:-------:|:------:|
| View Dashboard | ✓ | ✓ | ✓ | ✓ |
| Manage Inventory | ✓ | ✓ | ✗ | ✗ |
| Manage Vendors | ✓ | ✓ | ✗ | ✗ |
| Create POs | ✓ | ✓ | ✗ | ✗ |
| View Predictions | ✓ | ✓ | ✓ | ✓ |
| Run ML Models | ✓ | ✗ | ✓ | ✗ |
| Generate Reports | ✓ | ✓ | ✓ | ✗ |
| Manage Users | ✓ | ✗ | ✗ | ✗ |
| View Audit Logs | ✓ | ✗ | ✗ | ✗ |
| System Settings | ✓ | ✗ | ✗ | ✗ |

---

## File Structure

```
frontend/
├── js/
│   └── views/
│       └── dashboard/
│           ├── dashboard.view.js              # Main router
│           ├── supply-manager-dashboard.view.js
│           ├── analyst-dashboard.view.js
│           └── viewer-dashboard.view.js
├── css/
│   ├── app.css                                # Main styles
│   └── dashboard-roles.css                    # Dashboard-specific styles (NEW)
└── index.html                                 # Includes new CSS
```

---

## Styling

### CSS Features
- **Responsive Design:** Works on desktop (1920px), tablet (768px), and mobile (480px)
- **Role-Specific Colors:**
  - Supply Manager: Green (#10b981) - operations focused
  - Analyst: Indigo (#6366f1) - data focused
  - Viewer: Blue (#3b82f6) - simple and clean
- **Consistent Components:**
  - KPI Cards with icons
  - Charts (line, doughnut, bar)
  - Data tables with hover effects
  - Alert cards with severity indicators
  - Recommendation cards

### Key CSS Classes
- `.dashboard-card` - Base card styling
- `.kpi-card` - KPI card specific styles
- `.supply-manager-dashboard` - Supply manager theming
- `.analyst-dashboard` - Analyst theming
- `.viewer-dashboard` - Viewer theming
- `.dashboard-grid-3` - 3-column responsive grid
- `.dashboard-grid-2` - 2-column responsive grid
- `.table-container` - Responsive table wrapper

---

## Backend Integration Points

### Dashboard Service Methods
The dashboards use these service methods (update as needed):

```javascript
dashboardService.getInventoryStats()           // KPI data
dashboardService.getInventoryValueTrend()      // Line chart data
dashboardService.getStockoutRisk()             // Risk distribution
dashboardService.getTopRiskItems()             // Risk items table
dashboardService.getAlerts()                   // Active alerts
dashboardService.getCategories()               // Category breakdown
dashboardService.getPredictions()              // ML predictions
dashboardService.getSystemStats()              // Admin stats
dashboardService.getStockStatus()              // Supply manager
dashboardService.getVendorPerformance()        // Vendor metrics
dashboardService.getPurchaseOrders()           // PO tracking
dashboardService.getReorderPoints()            // Reorder alerts
dashboardService.getForecastAccuracy()         // Analyst metrics
dashboardService.getAnomalies()                // Detected issues
dashboardService.getInsights()                 // AI insights
dashboardService.getRecommendations()          // AI recommendations
```

---

## Setup Instructions

### 1. Verify Imports
Ensure all imports are in `frontend/js/router/routes.js`:

```javascript
import { renderDashboard } from "../views/dashboard/dashboard.view.js";
```

### 2. Link CSS
The CSS is already linked in `frontend/index.html`:

```html
<link rel="stylesheet" href="css/dashboard-roles.css" />
```

### 3. User Role Setup
Ensure users have correct roles set in the database:

```python
# Backend: app/models/user_model.py
roles = ["admin", "supply_manager", "analyst", "viewer"]
```

### 4. Test Dashboard
1. Log in with different user roles
2. Verify correct dashboard appears
3. Test responsive design on mobile

---

## Future Enhancements

### Planned Features
- [ ] Export dashboard data to PDF/Excel
- [ ] Custom dashboard widget arrangement
- [ ] Real-time data refresh intervals
- [ ] Dashboard sharing and scheduling
- [ ] Mobile app specific dashboards
- [ ] Voice commands for AI insights
- [ ] Advanced filtering options
- [ ] Drill-down capabilities

### Customization Options
- Modify KPI cards per role
- Add custom charts
- Create role-specific alerts
- Implement time-zone handling
- Add multi-language support

---

## Troubleshooting

### Dashboard Not Loading
**Issue:** Wrong dashboard appears or dashboard is blank

**Solutions:**
1. Check user role in localStorage: `JSON.parse(localStorage.getItem("user")).role`
2. Verify role matches one of: `admin`, `supply_manager`, `analyst`, `viewer`
3. Check browser console for errors
4. Clear cache and reload: `Ctrl+Shift+Delete`

### Charts Not Rendering
**Issue:** Chart containers show blank

**Solutions:**
1. Verify Chart.js is loaded: `window.Chart` should exist
2. Check dashboard service is returning data
3. Verify canvas IDs match the chart creation calls
4. Check for JavaScript errors in console

### Styling Issues
**Issue:** Dashboard looks wrong or missing styles

**Solutions:**
1. Verify CSS file is loaded: Check Network tab in DevTools
2. Clear browser cache: `Ctrl+Shift+Delete`
3. Check for CSS syntax errors in `dashboard-roles.css`
4. Verify media queries are correct for screen size

---

## Support

For issues or questions, check:
1. Browser console for errors
2. Backend logs for API issues
3. Network tab for failed requests
4. Browser DevTools responsive mode

---

Generated: 2026-07-01
Version: 1.0
