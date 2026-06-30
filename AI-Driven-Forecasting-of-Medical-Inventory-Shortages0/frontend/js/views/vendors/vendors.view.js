import { vendorService } from "../../services/vendor.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateVendorForm } from "../../utils/validation.js";

const view = document.getElementById("app");

let vendors = [];
let currentPage = 1;
let pageSize = 10;
let search = "";
let deletingId = null;

function skeletonVendors() {
  view.innerHTML = `
    <main class="crud-page">
      <div class="crud-header skeleton-box"></div>
      <div class="crud-toolbar skeleton-box"></div>
      <div class="crud-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function filteredVendors() {
  const query = search.toLowerCase();

  return vendors.filter(vendor =>
    vendor.name.toLowerCase().includes(query) ||
    String(vendor.contact_email || "").toLowerCase().includes(query) ||
    String(vendor.phone || "").toLowerCase().includes(query)
  );
}

function paginatedVendors() {
  const filtered = filteredVendors();
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;

  return {
    rows: filtered.slice(start, end),
    total: filtered.length,
    start,
    end
  };
}

function statusBadge(active) {
  return active
    ? `<span class="status-badge badge-success">Active</span>`
    : `<span class="status-badge badge-muted">Inactive</span>`;
}

function renderHeader() {
  return `
    <section class="crud-title-row">
      <div>
        <h1>Vendors</h1>
        <p>Manage medical suppliers, lead times, and contact information.</p>
      </div>

      <button id="addVendorBtn" class="primary-btn">
        + Add Vendor
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="crud-toolbar">
      <input
        id="vendorSearch"
        class="toolbar-input"
        value="${escapeHTML(search)}"
        placeholder="Search vendors by name, email, or phone..."
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedVendors();

  return `
    <section class="crud-card">
      <div class="table-wrapper">
        <table class="crud-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Lead Time</th>
              <th>Status</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((vendor, index) => renderRow(vendor, start + index + 1)).join("")
                : `<tr><td colspan="7" class="empty-row">No vendors found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevVendorPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextVendorPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(vendor, rowNumber) {
  if (deletingId === vendor.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="7">
          <strong>Delete ${escapeHTML(vendor.name)}?</strong>

          <button class="danger-btn small" data-confirm-vendor-delete="${vendor.id}">
            Yes, Delete
          </button>

          <button class="secondary-btn small" data-cancel-vendor-delete>
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
        <strong>${escapeHTML(vendor.name)}</strong>
      </td>

      <td>${escapeHTML(vendor.contact_email || "-")}</td>
      <td>${escapeHTML(vendor.phone || "-")}</td>
      <td>${vendor.lead_time_days} days</td>
      <td>${statusBadge(vendor.active)}</td>

      <td class="table-actions">
        <button class="icon-btn" data-edit-vendor="${vendor.id}">✎</button>
        <button class="icon-btn danger" data-delete-vendor="${vendor.id}">🗑</button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="vendorModal" class="crud-modal">
      <form id="vendorForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="vendorModalTitle">Add Vendor</h2>
          <button type="button" data-close-vendor-modal>×</button>
        </div>

        <div class="form-grid">
          <label>
          Vendor Code
          <input name="vendor_code" />
          </label>

          <label>
          Vendor Name
          <input name="name" />
          </label>

          <label>
          Email
          <input name="contact_email" type="email" />
          </label>

          <label>
          Phone
          <input name="contact_phone" />
          </label>

          <label>
          Lead Time
          <input
              name="avg_lead_time_days"
              type="number"
          />
          </label>

          <label>
          Reliability Score
          <input
              name="reliability_score"
              type="number"
              step="0.1"
              min="0"
              max="100"
          />
          </label>

          <label>
          Contract Expiry
          <input
              name="contract_expiry"
              type="date"
          />
          </label>

          <label>
          Street
          <input name="street" />
          </label>

          <label>
          City
          <input name="city" />
          </label>

          <label>
          State
          <input name="state" />
          </label>

          <label>
          Country
          <input name="country" />
          </label>

          <label>
          Pincode
          <input name="pincode" />
          </label>
          <label>
            Status
            <select name="active">
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
            <small data-error="active"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-vendor-modal>
            Cancel
          </button>

          <button id="submitVendorBtn" class="primary-btn">
            Save Vendor
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderVendorsPage() {
  view.innerHTML = `
    <main class="crud-page">
      ${renderHeader()}
      ${renderToolbar()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#vendorSearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderVendorsPage();
  });

  $("#prevVendorPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderVendorsPage();
  });

  $("#nextVendorPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderVendorsPage();
  });

  $("#addVendorBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-edit-vendor]").forEach(button => {
    button.addEventListener("click", () => {
      const vendor = vendors.find(row => String(row.id) === String(button.dataset.editVendor));
      openModal(vendor);
    });
  });

  document.querySelectorAll("[data-delete-vendor]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.deleteVendor);
      renderVendorsPage();
    });
  });

  $("[data-cancel-vendor-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderVendorsPage();
  });

  $("[data-confirm-vendor-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmVendorDelete);
  });

  document.querySelectorAll("[data-close-vendor-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#vendorModal").close();
    });
  });

  $("#vendorForm").addEventListener("submit", handleSubmit);
}

function openModal(vendor = null) {
  const modal = $("#vendorModal");
  const form = $("#vendorForm");

  form.reset();
  clearErrors();

  $("#vendorModalTitle").textContent = vendor ? "Edit Vendor" : "Add Vendor";

  if (vendor) {
    form.elements.id.value = vendor.id;
    form.elements.name.value = vendor.name || "";
    form.elements.contact_email.value = vendor.contact_email || "";
    form.elements.phone.value = vendor.phone || "";
    form.elements.lead_time_days.value = vendor.lead_time_days || "";
    form.elements.active.value = String(vendor.active);
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
    if (target) target.textContent = message;
  });
}

function getPayload(form) {
  const data = Object.fromEntries(new FormData(form).entries());

  return {
    vendor_code: (data.vendor_code || "").trim(),
    name: (data.name || "").trim(),
    contact_email: (data.contact_email || "").trim(),
    contact_phone: (data.contact_phone || "").trim() || null,
    avg_lead_time_days: Number(data.avg_lead_time_days || 0),
    reliability_score: Number(data.reliability_score || 0),
    contract_expiry: data.contract_expiry
      ? new Date(data.contract_expiry).toISOString()
      : null,
    address: {
      street: (data.street || "").trim(),
      city: (data.city || "").trim(),
      state: (data.state || "").trim(),
      country: (data.country || "").trim(),
      pincode: (data.pincode || "").trim()
    }
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const payload = getPayload(form);
  const errors = validateVendorForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitVendorBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (id) {
      await vendorService.updateVendor(id, payload);
    } else {
      await vendorService.createVendor(payload);
    }

    $("#vendorModal").close();
    await reloadVendors();

  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Vendor";
  }
}

async function handleDelete(id) {
  await vendorService.deleteVendor(id);
  deletingId = null;
  await reloadVendors();
}

async function reloadVendors() {
  vendors = await vendorService.getVendors();
  renderVendorsPage();
}

export async function renderVendors() {
  skeletonVendors();

  vendors = await vendorService.getVendors();

  renderVendorsPage();
}