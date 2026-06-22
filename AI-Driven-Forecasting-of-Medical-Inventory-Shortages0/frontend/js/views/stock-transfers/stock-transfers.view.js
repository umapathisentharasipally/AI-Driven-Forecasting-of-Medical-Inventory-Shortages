import { stockTransferService } from "../../services/stock-transfer.service.js";
import { inventoryService } from "../../services/inventory.service.js";
import { departmentService } from "../../services/department.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateStockTransferForm } from "../../utils/validation.js";

const view = document.getElementById("app");

let transfers = [];
let inventoryItems = [];
let departments = [];
let search = "";
let currentPage = 1;
let pageSize = 10;

function skeletonTransfers() {
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

function formatDate(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function filteredTransfers() {
  const query = search.toLowerCase();

  return transfers.filter(item =>
    String(item.transfer_no || "").toLowerCase().includes(query) ||
    String(item.from_department || "").toLowerCase().includes(query) ||
    String(item.to_department || "").toLowerCase().includes(query) ||
    String(item.item_name || "").toLowerCase().includes(query)
  );
}

function paginatedTransfers() {
  const filtered = filteredTransfers();
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
        <h1>Stock Transfers</h1>
        <p>Move medicines and supplies across departments with traceable logs.</p>
      </div>

      <button id="addTransferBtn" class="primary-btn">
        + Create Transfer
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="operations-toolbar">
      <input
        id="transferSearch"
        class="toolbar-input"
        placeholder="Search by transfer no, department, or item..."
        value="${escapeHTML(search)}"
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedTransfers();

  return `
    <section class="operations-card">
      <div class="table-wrapper">
        <table class="operations-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Transfer No.</th>
              <th>From Dept</th>
              <th>To Dept</th>
              <th>Item</th>
              <th>Items Count</th>
              <th>Quantity</th>
              <th>Date</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((transfer, index) =>
                    renderRow(transfer, start + index + 1)
                  ).join("")
                : `<tr><td colspan="8" class="empty-row">No stock transfers found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevTransferPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextTransferPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(transfer, rowNumber) {
  return `
    <tr>
      <td>${rowNumber}</td>

      <td>
        <code>${escapeHTML(transfer.transfer_no)}</code>
      </td>

      <td>${escapeHTML(transfer.from_department)}</td>
      <td>${escapeHTML(transfer.to_department)}</td>
      <td>${escapeHTML(transfer.item_name)}</td>
      <td>${transfer.items_count}</td>
      <td>${transfer.quantity}</td>
      <td>${formatDate(transfer.date)}</td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="transferModal" class="operations-modal">
      <form id="transferForm" method="dialog">
        <div class="modal-header">
          <h2>Create Stock Transfer</h2>
          <button type="button" data-close-transfer-modal>×</button>
        </div>

        <div class="form-grid">
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
            From Department
            <select name="from_department">
              <option value="">Select Department</option>
              ${departments.map(dept => {
                const name = dept.name || dept.department;
                return `<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`;
              }).join("")}
            </select>
            <small data-error="from_department"></small>
          </label>

          <label>
            To Department
            <select name="to_department">
              <option value="">Select Department</option>
              ${departments.map(dept => {
                const name = dept.name || dept.department;
                return `<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`;
              }).join("")}
            </select>
            <small data-error="to_department"></small>
          </label>

          <label>
            Quantity
            <input name="quantity" type="number" min="1" />
            <small data-error="quantity"></small>
          </label>

          <label>
            Date
            <input name="date" type="date" />
            <small data-error="date"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-transfer-modal>
            Cancel
          </button>

          <button id="submitTransferBtn" class="primary-btn">
            Save Transfer
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderTransfersPage() {
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
  $("#transferSearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderTransfersPage();
  });

  $("#prevTransferPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderTransfersPage();
  });

  $("#nextTransferPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderTransfersPage();
  });

  $("#addTransferBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-close-transfer-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#transferModal").close();
    });
  });

  $("#transferForm").addEventListener("submit", handleSubmit);
}

function openModal() {
  const modal = $("#transferModal");
  const form = $("#transferForm");

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
    item_id: Number(data.item_id),
    from_department: data.from_department,
    to_department: data.to_department,
    quantity: Number(data.quantity),
    date: data.date
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const payload = getPayload(form);
  const errors = validateStockTransferForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitTransferBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    await stockTransferService.createStockTransfer(payload);
    $("#transferModal").close();
    await reloadTransfers();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Transfer";
  }
}

async function reloadTransfers() {
  transfers = await stockTransferService.getStockTransfers();
  renderTransfersPage();
}

export async function renderStockTransfers() {
  skeletonTransfers();

  const [transferData, itemData, departmentData] = await Promise.all([
    stockTransferService.getStockTransfers(),
    inventoryService.getItems(),
    departmentService.getDepartments()
  ]);

  transfers = transferData;
  inventoryItems = itemData;
  departments = departmentData;

  renderTransfersPage();
}