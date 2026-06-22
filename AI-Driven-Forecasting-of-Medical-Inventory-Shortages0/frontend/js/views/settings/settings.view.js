import { settingsService } from "../../services/settings.service.js";
import { $, escapeHTML } from "../../utils/dom.js";
import {
  validateSettingsForm,
  validateProfileForm,
  validateChangePasswordForm
} from "../../utils/validation.js";
import { showToast } from "../../components/toast.js";

const view = document.getElementById("app");

let settings = {};
let profile = {};

function skeletonSettings() {
  view.innerHTML = `
    <main class="system-page">
      <div class="skeleton-box"></div>
      <div class="settings-grid">
        <div class="system-card skeleton-card"></div>
        <div class="system-card skeleton-card"></div>
      </div>
    </main>
  `;
}

function renderHeader() {
  return `
    <section class="system-title-row">
      <div>
        <h1>Settings</h1>
        <p>Configure system behavior, alert thresholds, profile, and security preferences.</p>
      </div>
    </section>
  `;
}

function renderSystemSettings() {
  return `
    <section class="system-card settings-panel">
      <h2>Application Settings</h2>

      <form id="settingsForm">
        <div class="form-grid">
          <label>
            Application Name
            <input name="app_name" value="${escapeHTML(settings.app_name || "MedInv Forecast")}" />
            <small data-error="app_name"></small>
          </label>

          <label>
            Low Stock Threshold
            <input name="low_stock_threshold" type="number" min="1" value="${settings.low_stock_threshold || 10}" />
            <small data-error="low_stock_threshold"></small>
          </label>

          <label>
            Expiry Alert Days
            <input name="expiry_alert_days" type="number" min="1" value="${settings.expiry_alert_days || 30}" />
            <small data-error="expiry_alert_days"></small>
          </label>

          <label>
            Default Currency
            <select name="currency">
              ${["USD", "INR", "EUR"].map(currency => `
                <option value="${currency}" ${settings.currency === currency ? "selected" : ""}>
                  ${currency}
                </option>
              `).join("")}
            </select>
          </label>

          <label>
            Enable Email Alerts
            <select name="email_alerts_enabled">
              <option value="true" ${settings.email_alerts_enabled !== false ? "selected" : ""}>Enabled</option>
              <option value="false" ${settings.email_alerts_enabled === false ? "selected" : ""}>Disabled</option>
            </select>
          </label>

          <label>
            Enable Auto Reorder Suggestions
            <select name="auto_reorder_enabled">
              <option value="true" ${settings.auto_reorder_enabled !== false ? "selected" : ""}>Enabled</option>
              <option value="false" ${settings.auto_reorder_enabled === false ? "selected" : ""}>Disabled</option>
            </select>
          </label>
        </div>

        <div class="modal-actions">
          <button id="saveSettingsBtn" class="primary-btn">
            Save Settings
          </button>
        </div>
      </form>
    </section>
  `;
}

function renderProfileSettings() {
  return `
    <section class="system-card settings-panel">
      <h2>Profile Settings</h2>

      <form id="profileForm">
        <div class="form-grid">
          <label>
            Full Name
            <input name="name" value="${escapeHTML(profile.name || "")}" />
            <small data-error="profile_name"></small>
          </label>

          <label>
            Email
            <input name="email" type="email" value="${escapeHTML(profile.email || "")}" />
            <small data-error="profile_email"></small>
          </label>

          <label>
            Role
            <input value="${escapeHTML(profile.role || "")}" disabled />
          </label>

          <label>
            Avatar URL
            <input name="avatar_url" value="${escapeHTML(profile.avatar_url || "")}" />
          </label>
        </div>

        <div class="modal-actions">
          <button id="saveProfileBtn" class="primary-btn">
            Save Profile
          </button>
        </div>
      </form>
    </section>
  `;
}

function renderPasswordSettings() {
  return `
    <section class="system-card settings-panel">
      <h2>Change Password</h2>

      <form id="passwordForm">
        <div class="form-grid">
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
        </div>

        <div class="modal-actions">
          <button id="changePasswordBtn" class="danger-btn">
            Change Password
          </button>
        </div>
      </form>
    </section>
  `;
}

function renderSettingsPage() {
  view.innerHTML = `
    <main class="system-page">
      ${renderHeader()}

      <section class="settings-grid">
        ${renderSystemSettings()}
        ${renderProfileSettings()}
      </section>

      ${renderPasswordSettings()}
    </main>
  `;

  bindEvents();
}

function bindEvents() {
  $("#settingsForm").addEventListener("submit", handleSettingsSubmit);
  $("#profileForm").addEventListener("submit", handleProfileSubmit);
  $("#passwordForm").addEventListener("submit", handlePasswordSubmit);
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function clearErrors() {
  document.querySelectorAll("[data-error]").forEach(error => {
    error.textContent = "";
  });
}

function showErrors(errors, prefix = "") {
  clearErrors();

  Object.entries(errors).forEach(([field, message]) => {
    const target =
      document.querySelector(`[data-error="${prefix}${field}"]`) ||
      document.querySelector(`[data-error="${field}"]`);

    if (target) target.textContent = message;
  });
}

async function handleSettingsSubmit(event) {
  event.preventDefault();

  const data = formData(event.target);

  const payload = {
    app_name: data.app_name.trim(),
    low_stock_threshold: Number(data.low_stock_threshold),
    expiry_alert_days: Number(data.expiry_alert_days),
    currency: data.currency,
    email_alerts_enabled: data.email_alerts_enabled === "true",
    auto_reorder_enabled: data.auto_reorder_enabled === "true"
  };

  const errors = validateSettingsForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  $("#saveSettingsBtn").disabled = true;
  $("#saveSettingsBtn").textContent = "Saving...";

  try {
    await settingsService.updateSettings(payload);
    showToast("Settings updated successfully", "success");
  } finally {
    $("#saveSettingsBtn").disabled = false;
    $("#saveSettingsBtn").textContent = "Save Settings";
  }
}

async function handleProfileSubmit(event) {
  event.preventDefault();

  const data = formData(event.target);

  const payload = {
    name: data.name.trim(),
    email: data.email.trim(),
    avatar_url: data.avatar_url?.trim() || null
  };

  const errors = validateProfileForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors, "profile_");
    return;
  }

  $("#saveProfileBtn").disabled = true;
  $("#saveProfileBtn").textContent = "Saving...";

  try {
    await settingsService.updateProfile(payload);
    showToast("Profile updated successfully", "success");
  } finally {
    $("#saveProfileBtn").disabled = false;
    $("#saveProfileBtn").textContent = "Save Profile";
  }
}

async function handlePasswordSubmit(event) {
  event.preventDefault();

  const data = formData(event.target);

  const payload = {
    current_password: data.current_password,
    new_password: data.new_password,
    confirm_password: data.confirm_password
  };

  const errors = validateChangePasswordForm(payload);

  if (Object.keys(errors).length) {
    showErrors(errors);
    return;
  }

  $("#changePasswordBtn").disabled = true;
  $("#changePasswordBtn").textContent = "Changing...";

  try {
    await settingsService.changePassword(payload);
    event.target.reset();
    showToast("Password changed successfully", "success");
  } finally {
    $("#changePasswordBtn").disabled = false;
    $("#changePasswordBtn").textContent = "Change Password";
  }
}

export async function renderSettings() {
  skeletonSettings();

  const [settingsData, profileData] = await Promise.all([
    settingsService.getSettings(),
    settingsService.getProfile()
  ]);

  settings = settingsData || {};
  profile = profileData || {};

  renderSettingsPage();
}