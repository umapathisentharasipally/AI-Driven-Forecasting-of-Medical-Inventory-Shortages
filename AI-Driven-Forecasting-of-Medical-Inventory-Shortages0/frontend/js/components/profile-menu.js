import { settingsService } from "../services/settings.service.js";
import { logout } from "../auth/session.js";

export async function initProfileMenu() {
  const button = document.getElementById("profileMenuBtn");
  const panel = document.getElementById("profileMenuPanel");

  if (!button || !panel) return;

  try {
    let response = await settingsService.getProfile();

    const profile = response?.data || response || {};

    const name =
      profile.full_name ||
      profile.name ||
      profile.username ||
      profile.email ||
      "User";

    const role =
      profile.role ||
      profile.role_name ||
      "User";

    const avatarUrl =
      profile.avatar_url ||
      null;

    const initials = name
      .split(" ")
      .map((x) => x[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();

    button.innerHTML = `
      <span class="profile-avatar">
        ${
          avatarUrl
            ? `<img src="${avatarUrl}" alt="${name}" />`
            : initials
        }
      </span>

      <span>
        <strong>${name}</strong>
        <small>${role}</small>
      </span>
    `;

    panel.innerHTML = `
      <button data-nav="profile">
        Profile
      </button>

      <button data-nav="settings">
        Settings
      </button>

      <button id="logoutBtn">
        Logout
      </button>
    `;

    button.addEventListener("click", () => {
      panel.classList.toggle("hidden");
    });

    document
      .getElementById("logoutBtn")
      ?.addEventListener("click", logout);

  } catch (error) {
    console.error(
      "Failed to initialize profile menu",
      error
    );
  }
}