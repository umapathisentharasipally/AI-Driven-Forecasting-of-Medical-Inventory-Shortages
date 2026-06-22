import { stockReceiptService } from "../../services/stock-receipt.service.js";
import { vendorService } from "../../services/vendor.service.js";
import { inventoryService } from "../../services/inventory.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateStockReceiptForm } from "../../utils/validation.js";

const view = document.getElementById("app");

let receipts = [];
let vendors = [];
let inventoryItems = [];
let search = "";
let currentPage = 1;
const pageSize = 10;

function skeletonReceipts() {
  view.innerHTML = `
    <main class="receipts-page">
      <div class="skeleton-box"></div>
      <div class="skeleton-box"></div>
      <div class="receipts-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function formatDate(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function filteredReceipts() {
  const query = search.toLowerCase();

  return receipts.filter(receipt =>
    String(receipt.receipt_no || "").toLowerCase().includes(query) ||
    String(receipt.vendor_name || "").toLowerCase().includes(query) ||
    String(receipt.item_name || "").toLowerCase().includes(query)
  );
}

function paginatedReceipts() {
  const filtered = filteredReceipts();
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
    <section class="receipts-title-row">
      <div>
        <h1>Receive Items</h1>
        <p>Record incoming stock receipts from vendors and update inventory batches.</p>
      </div>

      <button id="addReceiptBtn" class="primary-btn">
        + Receive Stock
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="receipts-toolbar">
      <input
        id="receiptSearch"
        class="toolbar-input"
        placeholder="Search by receipt number, vendor, or item..."
        value="${escapeHTML(search)}"
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedReceipts();

  return `
    <section class="receipts-card">
      <div class="table-wrapper">
        <table class="receipts-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Receipt No.</th>
              <th>Vendor</th>
              <th>Item</th>
              <th>Items Count</th>
              <th>Quantity</th>
              <th>Batch No.</th>
              <th>Received Date</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((receipt, index) => renderRow(receipt, start + index + 1)).join("")
                : `<tr><td colspan="8" class="empty-row">No stock receipts found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevReceiptPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextReceiptPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(receipt, rowNumber) {
  return `
    <tr>
      <td>${rowNumber}</td>

      <td>
        <code>${escapeHTML(receipt.receipt_no)}</code>
      </td>

      <td>${escapeHTML(receipt.vendor_name)}</td>
      <td>${escapeHTML(receipt.item_name || "-")}</td>
      <td>${receipt.items_count ?? 1}</td>
      <td>${receipt.quantity}</td>
      <td>${escapeHTML(receipt.batch_no || "-")}</td>
      <td>${formatDate(receipt.received_date)}</td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="receiptModal" class="receipts-modal">
      <form id="receiptForm" method="dialog">

        <div class="modal-header">
          <h2>Receive Stock</h2>
          <button type="button" data-close-receipt-modal>×</button>
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
            Batch No.
            <input name="batch_no" type="text" />
            <small data-error="batch_no"></small>
          </label>

          <label>
            Received Date
            <input name="received_date" type="date" />
            <small data-error="received_date"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-receipt-modal>
            Cancel
          </button>

          <button id="submitReceiptBtn" class="primary-btn">
            Save Receipt
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderReceiptsPage() {
  view.innerHTML = `
    <main class="receipts-page">
      ${renderHeader()}
      ${renderToolbar()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#receiptSearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderReceiptsPage();
  });

  $("#prevReceiptPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderReceiptsPage();
  });

  $("#nextReceiptPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderReceiptsPage();
  });

  $("#addReceiptBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-close-receipt-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#receiptModal").close();
    });
  });

  $("#receiptForm").addEventListener("submit", handleSubmit);
}

function openModal() {
  const modal = $("#receiptModal");
  const form = $("#receiptForm");

  form.reset();
  clearErrors();
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
    batch_no: data.batch_no.trim().toUpperCase(),
    received_date: data.received_date
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const payload = getPayload(form);
  const errors = validateStockReceiptForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitReceiptBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    await stockReceiptService.createReceipt(payload);
    $("#receiptModal").close();
    await reloadReceipts();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Receipt";
  }
}

async function reloadReceipts() {
  receipts = await stockReceiptService.getReceipts();
  renderReceiptsPage();
}

export async function renderStockReceipts() {
  skeletonReceipts();

  const [receiptData, vendorData, itemData] = await Promise.all([
    stockReceiptService.getReceipts(),
    vendorService.getVendors(),
    inventoryService.getItems()
  ]);

  receipts = receiptData;
  vendors = vendorData;
  inventoryItems = itemData;

  renderReceiptsPage();
}