import { roleService } from "../../services/role.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateRoleForm } from "../../utils/validation.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let roles = [];
let permissions = [];
let deletingId = null;

function skeletonRoles() {
  view.innerHTML = `
    <main class="users-page">
      <div class="skeleton-box"></div>
      <div class="users-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function renderHeader() {
  return `
    <section class="users-title-row">
      <div>
        <h1>Roles & Permissions</h1>
        <p>Create roles and assign permission access for each module.</p>
      </div>

      <button id="addRoleBtn" class="primary-btn">
        + Add Role
      </button>
    </section>
  `;
}

function renderTable() {
  return `
    <section class="users-card">
      <div class="table-wrapper">
        <table class="users-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Role Name</th>
              <th>Description</th>
              <th>Permissions</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              roles.length
                ? roles.map((role, index) => renderRow(role, index + 1)).join("")
                : `<tr><td colspan="5" class="empty-row">No roles found</td></tr>`
            }
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderRow(role, rowNumber) {
  if (deletingId === role.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="5">
          <strong>Delete role ${escapeHTML(role.name)}?</strong>

          <button class="danger-btn small" data-confirm-role-delete="${role.id}">
            Yes, Delete
          </button>

          <button class="secondary-btn small" data-cancel-role-delete>
            Cancel
          </button>
        </td>
      </tr>
    `;
  }

  const rolePermissions = Array.isArray(role.permissions)
    ? role.permissions
    : [];

  return `
    <tr>
      <td>${rowNumber}</td>
      <td><strong>${escapeHTML(role.name)}</strong></td>
      <td>${escapeHTML(role.description || "-")}</td>
      <td>
        <div class="permission-chip-wrap">
          ${rolePermissions.slice(0, 5).map(permission => `
            <span class="permission-chip">${escapeHTML(permission)}</span>
          `).join("")}

          ${
            rolePermissions.length > 5
              ? `<span class="permission-chip">+${rolePermissions.length - 5}</span>`
              : ""
          }
        </div>
      </td>

      <td class="table-actions">
        <button class="icon-btn" data-edit-role="${role.id}">✎</button>
        <button class="icon-btn danger" data-delete-role="${role.id}">🗑</button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="roleModal" class="users-modal">
      <form id="roleForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="roleModalTitle">Add Role</h2>
          <button type="button" data-close-role-modal>×</button>
        </div>

        <div class="form-grid single">
          <label>
            Role Name
            <input name="name" type="text" />
            <small data-error="name"></small>
          </label>

          <label>
            Description
            <textarea name="description" rows="4"></textarea>
            <small data-error="description"></small>
          </label>

          <div>
            <p class="permission-title">Permissions</p>
            <div class="permission-grid">
              ${permissions.map(permission => `
                <label class="permission-option">
                  <input 
                    type="checkbox" 
                    name="permissions" 
                    value="${escapeHTML(permission.code || permission)}" />
                  <span>${escapeHTML(permission.label || permission.name || permission)}</span>
                </label>
              `).join("")}
            </div>
            <small data-error="permissions"></small>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-role-modal>
            Cancel
          </button>

          <button id="submitRoleBtn" class="primary-btn">
            Save Role
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderRolesPage() {
  view.innerHTML = `
    <main class="users-page">
      ${renderHeader()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#addRoleBtn").addEventListener("click", () => openModal());

  document.querySelectorAll("[data-edit-role]").forEach(button => {
    button.addEventListener("click", () => {
      const role = roles.find(row => String(row.id) === String(button.dataset.editRole));
      openModal(role);
    });
  });

  document.querySelectorAll("[data-delete-role]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.deleteRole);
      renderRolesPage();
    });
  });

  $("[data-cancel-role-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderRolesPage();
  });

  $("[data-confirm-role-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmRoleDelete);
  });

  document.querySelectorAll("[data-close-role-modal]").forEach(button => {
    button.addEventListener("click", () => $("#roleModal").close());
  });

  $("#roleForm").addEventListener("submit", handleSubmit);
}

function openModal(role = null) {
  const modal = $("#roleModal");
  const form = $("#roleForm");

  form.reset();
  clearErrors();

  $("#roleModalTitle").textContent = role ? "Edit Role" : "Add Role";

  if (role) {
    form.elements.id.value = role.id;
    form.elements.name.value = role.name || "";
    form.elements.description.value = role.description || "";

    const rolePermissions = Array.isArray(role.permissions)
      ? role.permissions
      : [];

    document
      .querySelectorAll('input[name="permissions"]')
      .forEach(input => {
        input.checked = rolePermissions.includes(input.value);
      });
  }

  modal.showModal();
}

function getPayload(form) {
  const data = new FormData(form);

  return {
    name: data.get("name").trim(),
    description: data.get("description")?.trim() || null,
    permissions: data.getAll("permissions")
  };
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

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const payload = getPayload(form);
  const errors = validateRoleForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitRoleBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (id) {
      await roleService.updateRole(id, payload);
      showToast("Role updated successfully", "success");
    } else {
      await roleService.createRole(payload);
      showToast("Role created successfully", "success");
    }

    $("#roleModal").close();
    await reloadRoles();

  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Role";
  }
}

async function handleDelete(id) {
  await roleService.deleteRole(id);
  deletingId = null;
  showToast("Role deleted successfully", "success");
  await reloadRoles();
}

async function reloadRoles() {
  roles = await roleService.getRoles();
  renderRolesPage();
}

export async function renderRoles() {
  skeletonRoles();

  const [roleData, permissionData] = await Promise.all([
    roleService.getRoles(),
    roleService.getPermissions()
  ]);

  roles = roleData;
  permissions = permissionData;

  renderRolesPage();
}