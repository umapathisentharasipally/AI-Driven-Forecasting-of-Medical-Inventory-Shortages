import { userService } from "../../services/user.service.js";
import { roleService } from "../../services/role.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateUserForm } from "../../utils/validation.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let users = [];
let roles = [];
let search = "";
let currentPage = 1;
const pageSize = 10;
let deletingId = null;

function skeletonUsers() {
  view.innerHTML = `
    <main class="users-page">
      <div class="skeleton-box"></div>
      <div class="users-card">
        ${Array.from({ length: 8 }).map(() => `<div class="skeleton-row"></div>`).join("")}
      </div>
    </main>
  `;
}

function statusBadge(isActive) {
  return isActive
    ? `<span class="status-badge badge-success">Active</span>`
    : `<span class="status-badge badge-danger">Inactive</span>`;
}

function filteredUsers() {
  const query = search.toLowerCase();

  return users.filter(user =>
    String(user.name || "").toLowerCase().includes(query) ||
    String(user.email || "").toLowerCase().includes(query) ||
    String(user.role_name || user.role || "").toLowerCase().includes(query)
  );
}

function paginatedUsers() {
  const filtered = filteredUsers();
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
    <section class="users-title-row">
      <div>
        <h1>Users</h1>
        <p>Manage system users, access status, and assigned roles.</p>
      </div>

      <button id="addUserBtn" class="primary-btn">
        + Add User
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="users-toolbar">
      <input
        id="userSearch"
        class="toolbar-input"
        placeholder="Search users by name, email, or role..."
        value="${escapeHTML(search)}"
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedUsers();

  return `
    <section class="users-card">
      <div class="table-wrapper">
        <table class="users-table">
          <thead>
            <tr>
              <th>#</th>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((user, index) => renderRow(user, start + index + 1)).join("")
                : `<tr><td colspan="7" class="empty-row">No users found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}</p>

        <div>
          <button id="prevUserPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextUserPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(user, rowNumber) {
  if (deletingId === user.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="7">
          <strong>Delete ${escapeHTML(user.name)}?</strong>

          <button class="danger-btn small" data-confirm-user-delete="${user.id}">
            Yes, Delete
          </button>

          <button class="secondary-btn small" data-cancel-user-delete>
            Cancel
          </button>
        </td>
      </tr>
    `;
  }

  const initials = String(user.name || "U")
    .split(" ")
    .map(part => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return `
    <tr>
      <td>${rowNumber}</td>

      <td>
        <div class="user-cell">
          <span class="user-avatar">
            ${
              user.avatar_url
                ? `<img src="${escapeHTML(user.avatar_url)}" alt="${escapeHTML(user.name)}" />`
                : initials
            }
          </span>

          <div>
            <strong>${escapeHTML(user.name)}</strong>
            <small>${escapeHTML(user.department || "No Department")}</small>
          </div>
        </div>
      </td>

      <td>${escapeHTML(user.email)}</td>
      <td>${escapeHTML(user.role_name || user.role)}</td>
      <td>${statusBadge(user.is_active)}</td>
      <td>${escapeHTML(user.last_login || "-")}</td>

      <td class="table-actions">
        <button class="icon-btn" data-edit-user="${user.id}">✎</button>

        <button 
          class="icon-btn ${user.is_active ? "danger" : ""}" 
          data-toggle-user="${user.id}">
          ${user.is_active ? "Deactivate" : "Activate"}
        </button>

        <button class="icon-btn danger" data-delete-user="${user.id}">
          🗑
        </button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="userModal" class="users-modal">
      <form id="userForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="userModalTitle">Add User</h2>
          <button type="button" data-close-user-modal>×</button>
        </div>

        <div class="form-grid">
          <label>
            Full Name
            <input name="name" type="text" />
            <small data-error="name"></small>
          </label>

          <label>
            Email
            <input name="email" type="email" />
            <small data-error="email"></small>
          </label>

          <label>
            Role
            <select name="role_id">
              <option value="">Select Role</option>
              ${roles.map(role => `
                <option value="${role.id}">
                  ${escapeHTML(role.name)}
                </option>
              `).join("")}
            </select>
            <small data-error="role_id"></small>
          </label>

          <label>
            Department
            <input name="department" type="text" />
            <small data-error="department"></small>
          </label>

          <label id="passwordField">
            Password
            <input name="password" type="password" />
            <small data-error="password"></small>
          </label>

          <label>
            Status
            <select name="is_active">
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-user-modal>
            Cancel
          </button>

          <button id="submitUserBtn" class="primary-btn">
            Save User
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderUsersPage() {
  view.innerHTML = `
    <main class="users-page">
      ${renderHeader()}
      ${renderToolbar()}
      ${renderTable()}
      ${renderModal()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#userSearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderUsersPage();
  });

  $("#prevUserPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderUsersPage();
  });

  $("#nextUserPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderUsersPage();
  });

  $("#addUserBtn").addEventListener("click", () => openModal());

  document.querySelectorAll("[data-edit-user]").forEach(button => {
    button.addEventListener("click", () => {
      const user = users.find(row => String(row.id) === String(button.dataset.editUser));
      openModal(user);
    });
  });

  document.querySelectorAll("[data-toggle-user]").forEach(button => {
    button.addEventListener("click", async () => {
      const user = users.find(row => String(row.id) === String(button.dataset.toggleUser));
      await toggleUserStatus(user);
    });
  });

  document.querySelectorAll("[data-delete-user]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.deleteUser);
      renderUsersPage();
    });
  });

  $("[data-cancel-user-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderUsersPage();
  });

  $("[data-confirm-user-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmUserDelete);
  });

  document.querySelectorAll("[data-close-user-modal]").forEach(button => {
    button.addEventListener("click", () => $("#userModal").close());
  });

  $("#userForm").addEventListener("submit", handleSubmit);
}

function openModal(user = null) {
  const modal = $("#userModal");
  const form = $("#userForm");

  form.reset();
  clearErrors();

  $("#userModalTitle").textContent = user ? "Edit User" : "Add User";

  if (user) {
    form.elements.id.value = user.id;
    form.elements.name.value = user.name || "";
    form.elements.email.value = user.email || "";
    form.elements.role_id.value = user.role_id || "";
    form.elements.department.value = user.department || "";
    form.elements.is_active.value = String(user.is_active);
    $("#passwordField").style.display = "none";
  } else {
    $("#passwordField").style.display = "grid";
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

function getPayload(form, isEdit) {
  const data = Object.fromEntries(new FormData(form).entries());

  const payload = {
    name: data.name.trim(),
    email: data.email.trim(),
    role_id: Number(data.role_id),
    department: data.department?.trim() || null,
    is_active: data.is_active === "true"
  };

  if (!isEdit) {
    payload.password = data.password;
  }

  return payload;
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const isEdit = Boolean(id);
  const payload = getPayload(form, isEdit);
  const errors = validateUserForm(payload, isEdit);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitUserBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (isEdit) {
      await userService.updateUser(id, payload);
      showToast("User updated successfully", "success");
    } else {
      await userService.createUser(payload);
      showToast("User created successfully", "success");
    }

    $("#userModal").close();
    await reloadUsers();

  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save User";
  }
}

async function toggleUserStatus(user) {
  await userService.updateUserStatus(user.id, {
    is_active: !user.is_active
  });

  showToast("User status updated", "success");
  await reloadUsers();
}

async function handleDelete(id) {
  await userService.deleteUser(id);
  deletingId = null;
  showToast("User deleted successfully", "success");
  await reloadUsers();
}

async function reloadUsers() {
  users = await userService.getUsers();
  renderUsersPage();
}

export async function renderUsers() {
  skeletonUsers();

  const [userData, roleData] = await Promise.all([
    userService.getUsers(),
    roleService.getRoles()
  ]);

  users = userData;
  roles = roleData;

  renderUsersPage();
}