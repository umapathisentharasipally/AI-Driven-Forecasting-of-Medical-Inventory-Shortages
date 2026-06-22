import { categoryService } from "../../services/category.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import { validateCategoryForm } from "../../utils/validation.js";


const view = document.getElementById("app");

let categories = [];
let currentPage = 1;
let pageSize = 10;
let search = "";
let deletingId = null;

function skeletonCategories() {
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

function filteredCategories() {
  return categories.filter(category => {
    const query = search.toLowerCase();

    return (
      category.name.toLowerCase().includes(query) ||
      String(category.description || "").toLowerCase().includes(query)
    );
  });
}

function paginatedCategories() {
  const filtered = filteredCategories();
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
    <section class="crud-title-row">
      <div>
        <h1>Categories</h1>
        <p>Manage medical inventory categories and stock classification groups.</p>
      </div>

      <button id="addCategoryBtn" class="primary-btn">
        + Add Category
      </button>
    </section>
  `;
}

function renderToolbar() {
  return `
    <section class="crud-toolbar">
      <input
        id="categorySearch"
        class="toolbar-input"
        value="${escapeHTML(search)}"
        placeholder="Search categories..."
      />
    </section>
  `;
}

function renderTable() {
  const { rows, total, start, end } = paginatedCategories();

  return `
    <section class="crud-card">
      <div class="table-wrapper">
        <table class="crud-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Description</th>
              <th>Item Count</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            ${
              rows.length
                ? rows.map((category, index) =>
                    renderRow(category, start + index + 1)
                  ).join("")
                : `<tr><td colspan="5" class="empty-row">No categories found</td></tr>`
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p>
          Showing ${total === 0 ? 0 : start + 1}–${Math.min(end, total)} of ${total}
        </p>

        <div>
          <button id="prevCategoryPage" ${currentPage === 1 ? "disabled" : ""}>Prev</button>
          <span>Page ${currentPage}</span>
          <button id="nextCategoryPage" ${end >= total ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </section>
  `;
}

function renderRow(category, rowNumber) {
  if (deletingId === category.id) {
    return `
      <tr class="delete-confirm-row">
        <td colspan="5">
          <strong>Delete ${escapeHTML(category.name)}?</strong>

          <button class="danger-btn small" data-confirm-category-delete="${category.id}">
            Yes, Delete
          </button>

          <button class="secondary-btn small" data-cancel-category-delete>
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
        <strong>${escapeHTML(category.name)}</strong>
      </td>

      <td>${escapeHTML(category.description || "-")}</td>

      <td>
        <span class="count-badge">${category.item_count ?? 0}</span>
      </td>

      <td class="table-actions">
        <button class="icon-btn" data-edit-category="${category.id}">✎</button>
        <button class="icon-btn danger" data-delete-category="${category.id}">🗑</button>
      </td>
    </tr>
  `;
}

function renderModal() {
  return `
    <dialog id="categoryModal" class="crud-modal">
      <form id="categoryForm" method="dialog">
        <input type="hidden" name="id" />

        <div class="modal-header">
          <h2 id="categoryModalTitle">Add Category</h2>
          <button type="button" data-close-category-modal>×</button>
        </div>

        <div class="form-grid single">
          <label>
            Category Name
            <input name="name" type="text" />
            <small data-error="name"></small>
          </label>

          <label>
            Description
            <textarea name="description" rows="5"></textarea>
            <small data-error="description"></small>
          </label>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-btn" data-close-category-modal>
            Cancel
          </button>

          <button id="submitCategoryBtn" class="primary-btn">
            Save Category
          </button>
        </div>
      </form>
    </dialog>
  `;
}

function renderCategoriesPage() {
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
  $("#categorySearch").addEventListener("input", event => {
    search = event.target.value;
    currentPage = 1;
    renderCategoriesPage();
  });

  $("#prevCategoryPage")?.addEventListener("click", () => {
    currentPage -= 1;
    renderCategoriesPage();
  });

  $("#nextCategoryPage")?.addEventListener("click", () => {
    currentPage += 1;
    renderCategoriesPage();
  });

  $("#addCategoryBtn").addEventListener("click", () => {
    openModal();
  });

  document.querySelectorAll("[data-edit-category]").forEach(button => {
    button.addEventListener("click", () => {
      const category = categories.find(row => String(row.id) === String(button.dataset.editCategory));
      openModal(category);
    });
  });

  document.querySelectorAll("[data-delete-category]").forEach(button => {
    button.addEventListener("click", () => {
      deletingId = Number(button.dataset.deleteCategory);
      renderCategoriesPage();
    });
  });

  $("[data-cancel-category-delete]")?.addEventListener("click", () => {
    deletingId = null;
    renderCategoriesPage();
  });

  $("[data-confirm-category-delete]")?.addEventListener("click", async event => {
    await handleDelete(event.target.dataset.confirmCategoryDelete);
  });

  document.querySelectorAll("[data-close-category-modal]").forEach(button => {
    button.addEventListener("click", () => {
      $("#categoryModal").close();
    });
  });

  $("#categoryForm").addEventListener("submit", handleSubmit);
}

function openModal(category = null) {
  const modal = $("#categoryModal");
  const form = $("#categoryForm");

  form.reset();
  clearErrors();

  $("#categoryModalTitle").textContent = category ? "Edit Category" : "Add Category";

  if (category) {
    form.elements.id.value = category.id;
    form.elements.name.value = category.name || "";
    form.elements.description.value = category.description || "";
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
    name: data.name.trim(),
    description: data.description?.trim() || null
  };
}

async function handleSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const id = form.elements.id.value;
  const payload = getPayload(form);
  const errors = validateCategoryForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  const submitBtn = $("#submitCategoryBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    if (id) {
      await categoryService.updateCategory(id, payload);
    } else {
      await categoryService.createCategory(payload);
    }

    $("#categoryModal").close();
    await reloadCategories();

  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Category";
  }
}

async function handleDelete(id) {
  await categoryService.deleteCategory(id);
  deletingId = null;
  await reloadCategories();
}

async function reloadCategories() {
  categories = await categoryService.getCategories();
  renderCategoriesPage();
}

export async function renderCategories() {
  skeletonCategories();

  categories = await categoryService.getCategories();

  renderCategoriesPage();
}