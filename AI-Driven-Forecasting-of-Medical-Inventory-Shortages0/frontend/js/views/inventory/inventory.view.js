import { inventoryService } from "../../services/inventory.service.js";
import { categoryService } from "../../services/category.service.js";
import { vendorService } from "../../services/vendor.service.js";
import { departmentService } from "../../services/department.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateInventoryForm } from "../../utils/validation.js";

const view = document.getElementById("app");

let inventoryItems = [];
let categories = [];
let vendors = [];
let departments = [];

let currentPage = 1;
let pageSize = 15;
let sortKey = "name";
let sortDirection = "asc";
let deletingId = null;

const state = {
  search: "",
  category: "",
  status: "",
  department: ""
};

function formatCurrency(value) {
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
    "In Stock": "badge-success",
    "Low Stock": "badge-warning",
    "Out of Stock": "badge-danger",
    Expired: "badge-muted"
  };

  return `<span class="status-badge ${map[status] || "badge-muted"}">${escapeHTML(status)}</span>`;
}

function inventorySkeleton() {
  view.innerHTML = `
    <main class="inventory-page">
      <div class="inventory-header skeleton-box"></div>
      <div class="inventory-toolbar skeleton-box"></div>
      <div class="inventory-card">
        ${Array.from({ length: 10 }).map(() => `
          <div class="skeleton-row"></div>
        `).join("")}
      </div>
    </main>
  `;
}

function getFilteredItems() {
  let data = [...inventoryItems];

  if (state.search) {
    const query = state.search.toLowerCase();

    data = data.filter(item =>
      item.name.toLowerCase().includes(query) ||
      item.sku.toLowerCase().includes(query)
    );
  }

  if (state.category) {
    data = data.filter(item => String(item.category_id) === String(state.category));
  }

  if (state.status) {
    data = data.filter(item => item.status === state.status);
  }

  if (state.department) {
    data = data.filter(item => item.department === state.department);
  }

  data.sort((a, b) => {
    const valueA = a[sortKey];
    const valueB = b[sortKey];

    if (valueA < valueB) {
      return sortDirection === "asc" ? -1 : 1;
    }

    if (valueA > valueB) {
      return sortDirection === "asc" ? 1 : -1;
    }

    return 0;
  });

  return data;
}

function getPaginatedItems() {
  const filtered = getFilteredItems();
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
    <section class="inventory-title-row">
      <div>
        <h1>Inventory Items</h1>
        <p>Manage medicines, stock levels, vendors, expiry, and reorder safety levels.</p>
      </div>

      <button id="addItemBtn" class="primary-btn">
        + Add Item
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="inventory-toolbar">
      <input 
        id="inventorySearch"
        class="toolbar-input"
        placeholder="Search by item name or SKU..."
        value="${escapeHTML(state.search)}"
      />

      <select id="categoryFilter" class="toolbar-select">
        <option value="">All Categories</option>
        ${categories.map(category => `
          <option value="${category.id}" ${String(state.category) === String(category.id) ? "selected" : ""}>
            ${escapeHTML(category.name)}
          </option>
        `).join("")}
      </select>

      <select id="statusFilter" class="toolbar-select">
        <option value="">All Status</option>
        ${["In Stock", "Low Stock", "Out of Stock", "Expired"].map(status => `
          <option value="${status}" ${state.status === status ? "selected" : ""}>
            ${status}
          </option>
        `).join("")}
      </select>

      <select id="departmentFilter" class="toolbar-select">
        <option value="">All Departments</option>
        ${departments.map(dept => `
          <option value="${escapeHTML(dept.name || dept.department)}" 
            ${state.department === (dept.name || dept.department) ? "selected" : ""}>
            ${escapeHTML(dept.name || dept.department)}
          </option>
        `).join("")}
      </select>
    </section>
  `;
}

function sortIcon(key) {
  if (sortKey !== key) return "↕";
  return sortDirection === "asc" ? "↑" : "↓";
}

function renderTable() {
  const { rows, total, start, end } = getPaginatedItems();

  return `
    <section class="inventory-card">
      <div class="table-wrapper">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>#</th>
              <th data-sort="name">Item Name ${sortIcon("name")}</th>
              <th>SKU</th>
              <th>Category</th>
              <th>Vendor</th>
              <th data-sort="unit_price">Unit Price ${sortIcon("unit_price")}</th>
              <th data-sort="quantity_on_hand">Qty ${sortIcon("quantity_on_hand")}</th>
              <th>Min Stock</th>
              <th>Status</th>
              <th>Expiry Date</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((item, index) => renderRow(item, start + index + 1)).join("")
                : `<tr><td colspan="11" class="empty-row">No inventory items found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevPageBtn" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextPageBtn" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(item, rowNumber) {
  if (deletingId === item.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="11">
          <strong>Delete ${escapeHTML(item.name)}?</strong>

          <button class="danger-btn small" data-confirm-delete="${item.id}">
            Yes, Delete
          </button>

          <button class="secondary-btn small" data-cancel-delete>
            Cancel
          </button>
        </td>
      </tr>
    `;
  }

  return `
    <tr>
      <td>${rowNumber}</td>

      <td>
        <strong>${escapeHTML(item.name)}</strong>
        <small>${escapeHTML(item.batch_no || "")}</small>
      </td>

      <td>
        <code>${escapeHTML(item.sku)}</code>
      </td>

      <td>${escapeHTML(item.category_name)}</td>
      <td>${escapeHTML(item.vendor_name)}</td>
      <td>${formatCurrency(item.unit_price)}</td>
      <td>${item.quantity_on_hand}</td>
      <td>${item.min_stock_level}</td>
      <td>${statusBadge(item.status)}</td>
      <td>${formatDate(item.expiry_date)}</td>

      <td class="table-actions">
        <button data-edit-id="${item.id}" class="icon-btn">✎</button>
        <button data-delete-id="${item.id}" class="icon-btn danger">🗑</button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="inventoryModal" class="inventory-modal">
      <form id="inventoryForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="modalTitle">Add Inventory Item</h2>
          <button type="button" data-close-modal>×</button>
        </div>

        <div class="form-grid">
          ${inputField("Item Name", "name", "text")}
          ${inputField("SKU", "sku", "text")}

          <label>
            Category
            <select name="category_id">
              <option value="">Select Category</option>
              ${categories.map(category => `
                <option value="${category.id}">${escapeHTML(category.name)}</option>
              `).join("")}
            </select>
            <small data-error="category_id"></small>
          </label>

          <label>
            Vendor
            <select name="vendor_id">
              <option value="">Select Vendor</option>
              ${vendors.map(vendor => `
                <option value="${vendor.id}">${escapeHTML(vendor.name)}</option>
              `).join("")}
            </select>
            <small data-error="vendor_id"></small>
          </label>

          <label>
            Department
            <select name="department">
              <option value="">Select Department</option>
              ${departments.map(dept => {
                const name = dept.name || dept.department;
                return `<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`;
              }).join("")}
            </select>
            <small data-error="department"></small>
          </label>

          ${inputField("Unit Price", "unit_price", "number", "0.01")}
          ${inputField("Quantity on Hand", "quantity_on_hand", "number")}
          ${inputField("Min Stock Level", "min_stock_level", "number")}
          ${inputField("Batch No.", "batch_no", "text", "", false)}
          ${inputField("Expiry Date", "expiry_date", "date", "", false)}

          <label>
            Status
            <select name="status">
              <option value="">Select Status</option>
              <option value="In Stock">In Stock</option>
              <option value="Low Stock">Low Stock</option>
              <option value="Out of Stock">Out of Stock</option>
              <option value="Expired">Expired</option>
            </select>
            <small data-error="status"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-modal>
            Cancel
          </button>

          <button id="submitInventoryBtn" class="primary-btn">
            Save Item
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function inputField(label, name, type, step = "", required = true) {
  return `
    <label>
      ${label}
      <input 
        name="${name}" 
        type="${type}" 
        ${step ? `step="${step}"` : ""}
        ${required ? "required" : ""}
      />
      <small data-error="${name}"></small>
    </label>
  `;
}

function renderInventoryPage() {
  view.innerHTML = `
    <main class="inventory-page">
      ${renderHeader()}
      ${renderToolbar()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindInventoryEvents();
}

function bindInventoryEvents() {
  $("#inventorySearch").addEventListener("input", event => {
    state.search = event.target.value;
    currentPage = 1;
    renderInventoryPage();
  });

  $("#categoryFilter").addEventListener("change", event => {
    state.category = event.target.value;
    currentPage = 1;
    renderInventoryPage();
  });

  $("#statusFilter").addEventListener("change", event => {
    state.status = event.target.value;
    currentPage = 1;
    renderInventoryPage();
  });

  $("#departmentFilter").addEventListener("change", event => {
    state.department = event.target.value;
    currentPage = 1;
    renderInventoryPage();
  });

  document.querySelectorAll("[data-sort]").forEach(header => {
    header.addEventListener("click", () => {
      const key = header.dataset.sort;

      if (sortKey === key) {
        sortDirection = sortDirection === "asc" ? "desc" : "asc";
      } else {
        sortKey = key;
        sortDirection = "asc";
      }

      renderInventoryPage();
    });
  });

  $("#prevPageBtn")?.addEventListener("click", () => {
    currentPage -= 1;
    renderInventoryPage();
  });

  $("#nextPageBtn")?.addEventListener("click", () => {
    currentPage += 1;
    renderInventoryPage();
  });

  $("#addItemBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-edit-id]").forEach(button => {
    button.addEventListener("click", () => {
      const item = inventoryItems.find(row => String(row.id) === String(button.dataset.editId));
      openModal(item);
    });
  });

  document.querySelectorAll("[data-delete-id]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.deleteId);
      renderInventoryPage();
    });
  });

  $("[data-cancel-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderInventoryPage();
  });

  $("[data-confirm-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmDelete);
  });

  document.querySelectorAll("[data-close-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#inventoryModal").close();
    });
  });

  $("#inventoryForm").addEventListener("submit", handleSubmit);
}

function openModal(item = null) {
  const modal = $("#inventoryModal");
  const form = $("#inventoryForm");

  form.reset();
  clearErrors();

  $("#modalTitle").textContent = item ? "Edit Inventory Item" : "Add Inventory Item";

  if (item) {
    Object.keys(item).forEach(key => {
      if (form.elements[key]) {
        form.elements[key].value = item[key] ?? "";
      }
    });
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

  Object.entries(errors).forEach(([key, message]) => {
    const target = document.querySelector(`[data-error="${key}"]`);

    if (target) {
      target.textContent = message;
    }
  });
}

function getFormPayload(form) {
  const data = Object.fromEntries(new FormData(form).entries());

  return {
    name: data.name.trim(),
    sku: data.sku.trim().toUpperCase(),
    category_id: Number(data.category_id),
    vendor_id: Number(data.vendor_id),
    department: data.department,
    unit_price: Number(data.unit_price),
    quantity_on_hand: Number(data.quantity_on_hand),
    min_stock_level: Number(data.min_stock_level),
    batch_no: data.batch_no?.trim() || null,
    expiry_date: data.expiry_date || null,
    status: data.status
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const payload = getFormPayload(form);
  const errors = validateInventoryForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitInventoryBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (id) {
      await inventoryService.updateItem(id, payload);
    } else {
      await inventoryService.createItem(payload);
    }

    $("#inventoryModal").close();
    await reloadInventory();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Item";
  }
}

async function handleDelete(id) {
  await inventoryService.deleteItem(id);
  deletingId = null;
  await reloadInventory();
}

async function reloadInventory() {
  inventoryItems = await inventoryService.getItems();
  renderInventoryPage();
}

export async function renderInventory() {
  inventorySkeleton();

  const [items, categoryData, vendorData, departmentData] = await Promise.all([
    inventoryService.getItems(),
    categoryService.getCategories(),
    vendorService.getVendors(),
    departmentService.getDepartments()
  ]);

  inventoryItems = items;
  categories = categoryData;
  vendors = vendorData;
  departments = departmentData;

  renderInventoryPage();
}