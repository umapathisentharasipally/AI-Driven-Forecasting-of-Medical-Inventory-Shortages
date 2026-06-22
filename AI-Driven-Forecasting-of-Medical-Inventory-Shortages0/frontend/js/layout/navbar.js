export function renderNavbar() {

    const navbar = document.getElementById("navbar");

    if (!navbar) return;

    navbar.innerHTML = `
    
    <div class="navbar-left">

        <div class="breadcrumbs">
            <span id="breadcrumbText">
                Dashboard
            </span>
        </div>

    </div>

    <div class="navbar-right">

        <div class="global-search-wrapper">

            <input
                id="globalSearch"
                class="global-search"
                placeholder="Search inventory, suppliers..."
            />

        </div>

        <button
            id="notificationBtn"
            class="navbar-icon-btn"
        >
            🔔

            <span
                id="notificationBadge"
                class="notification-badge"
                hidden
            ></span>

        </button>

        <div
            id="notificationPanel"
            class="notification-panel hidden"
        ></div>

        <button
            id="themeToggle"
            data-theme-toggle
            class="navbar-icon-btn"
        >
            🌙
        </button>

        <div class="profile-wrapper">

            <button
                id="profileMenuBtn"
                class="profile-button"
            >
            </button>

            <div
                id="profileMenuPanel"
                class="profile-menu hidden"
            ></div>

        </div>

    </div>

    `;
}