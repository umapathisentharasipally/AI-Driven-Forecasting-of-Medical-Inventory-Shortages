import { returnService } from "../../services/return.service.js";
import { inventoryService } from "../../services/inventory.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateReturnForm } from "../../utils/validators.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let returns = [];
let inventoryItems = [];
let search = "";

function skeletonReturns() {
  view.innerHTML = `
    <main class="crud-page">
      <div class="skeleton-box"></div>
      <div class="crud-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function filteredReturns() {
  const query = search.toLowerCase();

  return returns.filter(item =>
    String(item.return_id || "").toLowerCase().includes(query) ||
    String(item.item_name || "").toLowerCase().includes(query) ||
    String(item.reason || "").toLowerCase().includes(query)
  );
}

function renderReturnsPage() {
  const rows = filteredReturns();

  view.innerHTML = `
    <main class="crud-page">
      <section class="crud-title-row">
        <div>
          <h1>Return Management</h1>
          <p>Track returned, damaged, expired, or rejected inventory items.</p>
        </div>

        <button id="createReturnBtn" class="primary-btn">+ Create Return</button>
      </section>

      <section class="crud-toolbar">
        <input
          id="returnSearch"
          class="toolbar-input"
          placeholder="Search returns..."
          value="${escapeHTML(search)}"
        />
      </section>

      <section class="crud-card">
        <div class="table-wrapper">
          <table class="crud-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Return ID</th>
                <th>Item</th>
                <th>Quantity</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              ${
                rows.length
                  ? rows.map((item, index) => `
                    <tr>
                      <td>${index + 1}</td>
                      <td><code>${escapeHTML(item.return_id)}</code></td>
                      <td>${escapeHTML(item.item_name)}</td>
                      <td>${item.quantity}</td>
                      <td>${escapeHTML(item.reason)}</td>
                      <td><span class="status-badge badge-warning">${escapeHTML(item.status)}</span></td>
                    </tr>
                  `).join("")
                  : `<tr><td colspan="6" class="empty-row">No returns found</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </section>

      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function renderModal() {
  return `
    <dialog id="returnModal" class="crud-modal">
      <form id="returnForm" method="dialog">
        <div class="modal-header">
          <h2>Create Return</h2>
          <button type="button" data-close-modal>×</button>
        </div>

        <div class="form-grid">
          <label>
            Item
            <select name="item_id">
              <option value="">Select Item</option>
              ${inventoryItems.map(item => `
                <option value="${item.id}">${escapeHTML(item.name)}</option>
              `).join("")}
            </select>
            <small data-error="item_id"></small>
          </label>

          <label>
            Quantity
            <input name="quantity" type="number" min="1" />
            <small data-error="quantity"></small>
          </label>

          <label class="full">
            Reason
            <textarea name="reason" rows="4"></textarea>
            <small data-error="reason"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-modal>Cancel</button>
          <button id="submitReturnBtn" class="primary-btn">Save Return</button>
        </div>
      </form>
    </dialog>
  `;
}

function bindEvents() {
  $("#returnSearch").addEventListener("input", event => {
    search = event.target.value;
    renderReturnsPage();
  });

  $("#createReturnBtn").addEventListener("click", () => {
    $("#returnForm").reset();
    $("#returnModal").showModal();
  });

  document.querySelectorAll("[data-close-modal]").forEach(button => {
    button.addEventListener("click", () => $("#returnModal").close());
  });

  $("#returnForm").addEventListener("submit", handleSubmit);
}

async function handleSubmit(event) {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(event.target).entries());

  const payload = {
    item_id: Number(data.item_id),
    quantity: Number(data.quantity),
    reason: data.reason.trim()
  };

  const errors = validateReturnForm(payload);

  if (Object.keys(errors).length) {
    Object.entries(errors).forEach(([key, value]) => {
      const target = document.querySelector(`[data-error="${key}"]`);
      if (target) target.textContent = value;
    });
    return;
  }

  $("#submitReturnBtn").disabled = true;
  $("#submitReturnBtn").textContent = "Saving...";

  try {
    await returnService.createReturn(payload);
    $("#returnModal").close();
    showToast("Return created successfully", "success");
    await reloadReturns();
  } catch {
    showToast("Failed to create return", "error");
  } finally {
    $("#submitReturnBtn").disabled = false;
    $("#submitReturnBtn").textContent = "Save Return";
  }
}

async function reloadReturns() {
  returns = await returnService.getReturns();
  renderReturnsPage();
}

export async function renderReturnManagement() {
  skeletonReturns();

  try {
    const [returnData, itemData] = await Promise.all([
      returnService.getReturns(),
      inventoryService.getItems()
    ]);

    returns = returnData;
    inventoryItems = itemData;

    renderReturnsPage();
  } catch {
    view.innerHTML = `<div class="error-state">Failed to load return management.</div>`;
  }
}