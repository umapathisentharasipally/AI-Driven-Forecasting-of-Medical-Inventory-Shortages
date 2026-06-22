import { checkBackendHealth } from "../utils/health-check.js";
import { dashboardService } from "../services/dashboard.service.js";
import { inventoryService } from "../services/inventory.service.js";
import { categoryService } from "../services/category.service.js";
import { vendorService } from "../services/vendor.service.js";
import { purchaseOrderService } from "../services/purchase-order.service.js";
import { stockTransferService } from "../services/stock-transfer.service.js";
import { stockReceiptService } from "../services/stock-receipt.service.js";
import { alertService } from "../services/alert.service.js";
import { analyticsService } from "../services/analytics.service.js";
import { userService } from "../services/user.service.js";
import { roleService } from "../services/role.service.js";
import { runIntegrationDiagnostics } from "./js/diagnostics/integration-test.js";


const tests = [
  ["Backend Health", () => checkBackendHealth()],
  ["Dashboard Stats", () => dashboardService.getInventoryStats()],
  ["Inventory Items", () => inventoryService.getItems()],
  ["Categories", () => categoryService.getCategories()],
  ["Vendors", () => vendorService.getVendors()],
  ["Purchase Orders", () => purchaseOrderService.getPurchaseOrders()],
  ["Stock Transfers", () => stockTransferService.getStockTransfers()],
  ["Stock Receipts", () => stockReceiptService.getReceipts()],
  ["Alerts", () => alertService.getAlerts()],
  ["Analytics Predictions", () => analyticsService.getPredictions()],
  ["Users", () => userService.getUsers()],
  ["Roles", () => roleService.getRoles()]
];

export async function runIntegrationDiagnostics() {
  const results = [];

  for (const [name, runner] of tests) {
    try {
      const data = await runner();

      results.push({
        name,
        status: "passed",
        data
      });

    } catch (error) {
      results.push({
        name,
        status: "failed",
        error: error.message
      });
    }
  }

  console.table(results);

  return results;
}