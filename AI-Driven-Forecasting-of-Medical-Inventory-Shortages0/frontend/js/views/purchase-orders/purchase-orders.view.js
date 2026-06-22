import { purchaseOrderService } from "../../services/purchase-order.service.js";
import { vendorService } from "../../services/vendor.service.js";
import { inventoryService } from "../../services/inventory.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validatePurchaseOrderForm } from "../../utils/validation.js";

const view = document.getElementById("app");

let purchaseOrders = [];
let vendors = [];
let inventoryItems = [];
let search = "";
let currentPage = 1;
let pageSize = 10;

function skeletonPurchaseOrders() {
  view.innerHTML = `
    <main class="operations-page">
      <div class="operations-header skeleton-box"></div>
      <div class="operations-toolbar skeleton-box"></div>
      <div class="operations-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(Number(value || 0));
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function statusBadge(status) {
  const map = {
    Pending: "badge-warning",
    Approved: "badge-success",
    Shipped: "badge-info",
    Received: "badge-muted"
  };

  return `<span class="status-badge ${map[status] || "badge-muted"}">${escapeHTML(status)}</span>`;
}

function filteredOrders() {
  const query = search.toLowerCase();

  return purchaseOrders.filter(order =>
    String(order.po_number || "").toLowerCase().includes(query) ||
    String(order.vendor_name || "").toLowerCase().includes(query) ||
    String(order.status || "").toLowerCase().includes(query)
  );
}

function paginatedOrders() {
  const filtered = filteredOrders();
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;

  return {
    rows: filtered.slice(start, end),
    total: filtered.length,
    start,
    end
  };
}

function renderHeader() {
  return `
    <section class="operations-title-row">
      <div>
        <h1>Purchase Orders</h1>
        <p>Create, approve, and track restock purchase orders.</p>
      </div>

      <button id="addPurchaseOrderBtn" class="primary-btn">
        + Create Purchase Order
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="operations-toolbar">
      <input
        id="purchaseOrderSearch"
        class="toolbar-input"
        placeholder="Search by PO number, vendor, or status..."
        value="${escapeHTML(search)}"
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedOrders();

  return `
    <section class="operations-card">
      <div class="table-wrapper">
        <table class="operations-table">
          <thead>
            <tr>
              <th>#</th>
              <th>PO Number</th>
              <th>Vendor</th>
              <th>Status</th>
              <th>Expected Date</th>
              <th>Total Amount</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((order, index) => renderRow(order, start + index + 1)).join("")
                : `<tr><td colspan="7" class="empty-row">No purchase orders found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevPurchaseOrderPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextPurchaseOrderPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(order, rowNumber) {
  return `
    <tr>
      <td>${rowNumber}</td>

      <td>
        <code>${escapeHTML(order.po_number)}</code>
      </td>

      <td>${escapeHTML(order.vendor_name)}</td>
      <td>${statusBadge(order.status)}</td>
      <td>${formatDate(order.expected_date)}</td>
      <td>${money(order.total_amount)}</td>

      <td class="table-actions">
        <button class="icon-btn" data-edit-po="${order.id}">
          ✎
        </button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="purchaseOrderModal" class="operations-modal">
      <form id="purchaseOrderForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="purchaseOrderModalTitle">Create Purchase Order</h2>
          <button type="button" data-close-po-modal>×</button>
        </div>

        <div class="form-grid">
          <label>
            Vendor
            <select name="vendor_id">
              <option value="">Select Vendor</option>
              ${vendors.map(vendor => `
                <option value="${vendor.id}">
                  ${escapeHTML(vendor.name)}
                </option>
              `).join("")}
            </select>
            <small data-error="vendor_id"></small>
          </label>

          <label>
            Item
            <select name="item_id">
              <option value="">Select Item</option>
              ${inventoryItems.map(item => `
                <option value="${item.id}">
                  ${escapeHTML(item.name)}
                </option>
              `).join("")}
            </select>
            <small data-error="item_id"></small>
          </label>

          <label>
            Quantity
            <input name="quantity" type="number" min="1" />
            <small data-error="quantity"></small>
          </label>

          <label>
            Unit Price
            <input name="unit_price" type="number" min="0.01" step="0.01" />
            <small data-error="unit_price"></small>
          </label>

          <label>
            Expected Date
            <input name="expected_date" type="date" />
            <small data-error="expected_date"></small>
          </label>

          <label>
            Status
            <select name="status">
              <option value="">Select Status</option>
              <option value="Pending">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Shipped">Shipped</option>
              <option value="Received">Received</option>
            </select>
            <small data-error="status"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-po-modal>
            Cancel
          </button>

          <button id="submitPurchaseOrderBtn" class="primary-btn">
            Save Purchase Order
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderPurchaseOrdersPage() {
  view.innerHTML = `
    <main class="operations-page">
      ${renderHeader()}
      ${renderToolbar()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#purchaseOrderSearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderPurchaseOrdersPage();
  });

  $("#prevPurchaseOrderPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderPurchaseOrdersPage();
  });

  $("#nextPurchaseOrderPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderPurchaseOrdersPage();
  });

  $("#addPurchaseOrderBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-edit-po]").forEach(button => {
    button.addEventListener("click", () => {
      const order = purchaseOrders.find(row => String(row.id) === String(button.dataset.editPo));
      openModal(order);
    });
  });

  document.querySelectorAll("[data-close-po-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#purchaseOrderModal").close();
    });
  });

  $("#purchaseOrderForm").addEventListener("submit", handleSubmit);
}

function openModal(order = null) {
  const modal = $("#purchaseOrderModal");
  const form = $("#purchaseOrderForm");

  form.reset();
  clearErrors();

  $("#purchaseOrderModalTitle").textContent =
    order ? "Edit Purchase Order" : "Create Purchase Order";

  if (order) {
    form.elements.id.value = order.id;
    form.elements.vendor_id.value = order.vendor_id || "";
    form.elements.item_id.value = order.item_id || "";
    form.elements.quantity.value = order.quantity || "";
    form.elements.unit_price.value = order.unit_price || "";
    form.elements.expected_date.value = order.expected_date || "";
    form.elements.status.value = order.status || "";
  }

  modal.showModal();
}

function clearErrors() {
  document.querySelectorAll("[data-error]").forEach(error => {
    error.textContent = "";
  });
}

function showErrors(errors) {
  clearErrors();

  Object.entries(errors).forEach(([field, message]) => {
    const target = document.querySelector(`[data-error="${field}"]`);
    if (target) target.textContent = message;
  });
}

function getPayload(form) {
  const data = Object.fromEntries(new FormData(form).entries());

  return {
    vendor_id: Number(data.vendor_id),
    item_id: Number(data.item_id),
    quantity: Number(data.quantity),
    unit_price: Number(data.unit_price),
    expected_date: data.expected_date,
    status: data.status
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const payload = getPayload(form);
  const errors = validatePurchaseOrderForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitPurchaseOrderBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (id) {
      await purchaseOrderService.updatePurchaseOrder(id, payload);
    } else {
      await purchaseOrderService.createPurchaseOrder(payload);
    }

    $("#purchaseOrderModal").close();
    await reloadPurchaseOrders();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Purchase Order";
  }
}

async function reloadPurchaseOrders() {
  purchaseOrders = await purchaseOrderService.getPurchaseOrders();
  renderPurchaseOrdersPage();
}

export async function renderPurchaseOrders() {
  skeletonPurchaseOrders();

  const [orders, vendorData, itemData] = await Promise.all([
    purchaseOrderService.getPurchaseOrders(),
    vendorService.getVendors(),
    inventoryService.getItems()
  ]);

  purchaseOrders = orders;
  vendors = vendorData;
  inventoryItems = itemData;

  renderPurchaseOrdersPage();
}