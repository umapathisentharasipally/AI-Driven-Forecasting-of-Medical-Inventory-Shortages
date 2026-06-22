import { profileService } from "../../services/profile.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import {
  validateProfileForm,
  validatePasswordForm
} from "../../utils/validators.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let profile = {};

function skeletonProfile() {
  view.innerHTML = `
    <main class="profile-page">
      <div class="skeleton-box"></div>
      <div class="profile-grid">
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
      </div>
    </main>
  `;
}

function renderProfilePage() {
  view.innerHTML = `
    <main class="profile-page">
      <section class="crud-title-row">
        <div>
          <h1>My Profile</h1>
          <p>Manage your personal information and password.</p>
        </div>
      </section>

      <section class="profile-grid">
        <article class="profile-card">
          <div class="profile-avatar-large">
            ${
              profile.avatar_url
                ? `<img src="${escapeHTML(profile.avatar_url)}" alt="Profile" />`
                : escapeHTML(String(profile.name || "U").slice(0, 2).toUpperCase())
            }
          </div>

          <h2>${escapeHTML(profile.name || "-")}</h2>
          <p>${escapeHTML(profile.email || "-")}</p>
          <span class="status-badge badge-info">${escapeHTML(profile.role || "-")}</span>
        </article>

        <article class="profile-card">
          <h2>Edit Profile</h2>

          <form id="profileForm" class="form-grid single">
            <label>
              Name
              <input name="name" value="${escapeHTML(profile.name || "")}" />
              <small data-error="name"></small>
            </label>

            <label>
              Email
              <input name="email" type="email" value="${escapeHTML(profile.email || "")}" />
              <small data-error="email"></small>
            </label>

            <label>
              Avatar URL
              <input name="avatar_url" value="${escapeHTML(profile.avatar_url || "")}" />
            </label>

            <button id="saveProfileBtn" class="primary-btn">Save Profile</button>
          </form>
        </article>
      </section>

      <article class="profile-card">
        <h2>Change Password</h2>

        <form id="passwordForm" class="form-grid">
          <label>
            Current Password
            <input name="current_password" type="password" />
            <small data-error="current_password"></small>
          </label>

          <label>
            New Password
            <input name="new_password" type="password" />
            <small data-error="new_password"></small>
          </label>

          <label>
            Confirm Password
            <input name="confirm_password" type="password" />
            <small data-error="confirm_password"></small>
          </label>

          <button id="changePasswordBtn" class="danger-btn">Change Password</button>
        </form>
      </article>
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#profileForm").addEventListener("submit", handleProfileSubmit);
  $("#passwordForm").addEventListener("submit", handlePasswordSubmit);
}

function clearErrors() {
  document.querySelectorAll("[data-error]").forEach(item => {
    item.textContent = "";
  });
}

function showErrors(errors) {
  clearErrors();

  Object.entries(errors).forEach(([key, value]) => {
    const target = document.querySelector(`[data-error="${key}"]`);
    if (target) target.textContent = value;
  });
}

async function handleProfileSubmit(event) {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(event.target).entries());

  const payload = {
    name: data.name.trim(),
    email: data.email.trim(),
    avatar_url: data.avatar_url?.trim() || null
  };

  const errors = validateProfileForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  $("#saveProfileBtn").disabled = true;
  $("#saveProfileBtn").textContent = "Saving...";

  try {
    await profileService.updateProfile(payload);
    showToast("Profile updated successfully", "success");
    await reloadProfile();
  } catch {
    showToast("Failed to update profile", "error");
  } finally {
    $("#saveProfileBtn").disabled = false;
    $("#saveProfileBtn").textContent = "Save Profile";
  }
}

async function handlePasswordSubmit(event) {
  event.preventDefault();

  const payload = Object.fromEntries(new FormData(event.target).entries());
  const errors = validatePasswordForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  $("#changePasswordBtn").disabled = true;
  $("#changePasswordBtn").textContent = "Changing...";

  try {
    await profileService.changePassword(payload);
    event.target.reset();
    showToast("Password changed successfully", "success");
  } catch {
    showToast("Failed to change password", "error");
  } finally {
    $("#changePasswordBtn").disabled = false;
    $("#changePasswordBtn").textContent = "Change Password";
  }
}

async function reloadProfile() {
  profile = await profileService.getProfile();
  renderProfilePage();
}

export async function renderProfile() {
  skeletonProfile();

  try {
    profile = await profileService.getProfile();
    renderProfilePage();
  } catch {
    view.innerHTML = `<div class="error-state">Failed to load profile.</div>`;
  }
}