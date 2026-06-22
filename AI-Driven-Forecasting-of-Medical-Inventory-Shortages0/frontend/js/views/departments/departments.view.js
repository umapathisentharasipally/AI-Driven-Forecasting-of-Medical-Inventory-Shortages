import { departmentService } from "../../services/department.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateDepartmentForm } from "../../utils/validators.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let departments = [];
let search = "";
let deletingId = null;

function skeletonDepartments() {
  view.innerHTML = `
    <main class="crud-page">
      <div class="skeleton-box"></div>
      <div class="crud-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function filteredDepartments() {
  const query = search.toLowerCase();

  return departments.filter(item =>
    String(item.name || item.department || "").toLowerCase().includes(query)
  );
}

function renderDepartmentsPage() {
  const rows = filteredDepartments();

  view.innerHTML = `
    <main class="crud-page">
      <section class="crud-title-row">
        <div>
          <h1>Departments</h1>
          <p>Manage hospital departments used for inventory allocation.</p>
        </div>

        <button id="addDepartmentBtn" class="primary-btn">
          + Add Department
        </button>
      </section>

      <section class="crud-toolbar">
        <input
          id="departmentSearch"
          class="toolbar-input"
          placeholder="Search departments..."
          value="${escapeHTML(search)}"
        />
      </section>

      <section class="crud-card">
        <div class="table-wrapper">
          <table class="crud-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Department Name</th>
                <th>Description</th>
                <th>Status</th>
                <th class="text-right">Actions</th>
              </tr>
            </thead>

            <tbody>
              ${
                rows.length
                  ? rows.map((item, index) => renderRow(item, index + 1)).join("")
                  : `<tr><td colspan="5" class="empty-row">No departments found</td></tr>`
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

function renderRow(item, index) {
  const name = item.name || item.department;

  if (deletingId === item.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="5">
          <strong>Delete ${escapeHTML(name)}?</strong>
          <button class="danger-btn small" data-confirm-delete="${item.id}">Yes, Delete</button>
          <button class="secondary-btn small" data-cancel-delete>Cancel</button>
        </td>
      </tr>
    `;
  }

  return `
    <tr>
      <td>${index}</td>
      <td><strong>${escapeHTML(name)}</strong></td>
      <td>${escapeHTML(item.description || "-")}</td>
      <td><span class="status-badge badge-success">Active</span></td>
      <td class="table-actions">
        <button class="icon-btn" data-edit="${item.id}">✎</button>
        <button class="icon-btn danger" data-delete="${item.id}">🗑</button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="departmentModal" class="crud-modal">
      <form id="departmentForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="departmentModalTitle">Add Department</h2>
          <button type="button" data-close-modal>×</button>
        </div>

        <div class="form-grid single">
          <label>
            Department Name
            <input name="name" type="text" />
            <small data-error="name"></small>
          </label>

          <label>
            Description
            <textarea name="description" rows="4"></textarea>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-modal>Cancel</button>
          <button id="submitDepartmentBtn" class="primary-btn">Save Department</button>
        </div>
      </form>
    </dialog>
  `;
}

function bindEvents() {
  $("#departmentSearch").addEventListener("input", event => {
    search = event.target.value;
    renderDepartmentsPage();
  });

  $("#addDepartmentBtn").addEventListener("click", () => openModal());

  document.querySelectorAll("[data-edit]").forEach(button => {
    button.addEventListener("click", () => {
      const item = departments.find(row => String(row.id) === String(button.dataset.edit));
      openModal(item);
    });
  });

  document.querySelectorAll("[data-delete]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.delete);
      renderDepartmentsPage();
    });
  });

  $("[data-cancel-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderDepartmentsPage();
  });

  $("[data-confirm-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmDelete);
  });

  document.querySelectorAll("[data-close-modal]").forEach(button => {
    button.addEventListener("click", () => $("#departmentModal").close());
  });

  $("#departmentForm").addEventListener("submit", handleSubmit);
}

function openModal(item = null) {
  const modal = $("#departmentModal");
  const form = $("#departmentForm");

  form.reset();
  $("#departmentModalTitle").textContent = item ? "Edit Department" : "Add Department";

  if (item) {
    form.elements.id.value = item.id;
    form.elements.name.value = item.name || item.department || "";
    form.elements.description.value = item.description || "";
  }

  modal.showModal();
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;

  const payload = {
    name: form.elements.name.value.trim(),
    description: form.elements.description.value.trim() || null
  };

  const errors = validateDepartmentForm(payload);

  if (Object.keys(errors).length) {
    document.querySelector('[data-error="name"]').textContent = errors.name;
    return;
  }

  $("#submitDepartmentBtn").disabled = true;
  $("#submitDepartmentBtn").textContent = "Saving...";

  try {
    if (id) {
      await departmentService.updateDepartment(id, payload);
      showToast("Department updated successfully", "success");
    } else {
      await departmentService.createDepartment(payload);
      showToast("Department created successfully", "success");
    }

    $("#departmentModal").close();
    await reloadDepartments();
  } catch (error) {
    showToast("Failed to save department", "error");
  } finally {
    $("#submitDepartmentBtn").disabled = false;
    $("#submitDepartmentBtn").textContent = "Save Department";
  }
}

async function handleDelete(id) {
  try {
    await departmentService.deleteDepartment(id);
    deletingId = null;
    showToast("Department deleted successfully", "success");
    await reloadDepartments();
  } catch {
    showToast("Failed to delete department", "error");
  }
}

async function reloadDepartments() {
  departments = await departmentService.getDepartments();
  renderDepartmentsPage();
}

export async function renderDepartments() {
  skeletonDepartments();

  try {
    departments = await departmentService.getDepartments();
    renderDepartmentsPage();
  } catch {
    view.innerHTML = `<div class="error-state">Failed to load departments.</div>`;
  }
}