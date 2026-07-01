export function renderNavbar() {

    const navbar = document.getElementById("navbar");

    if (!navbar) return;

    navbar.innerHTML = `
    
    <div class="navbar-left">
        <button id="sidebarToggle" class="sidebar-toggle-btn" title="Toggle Menu">
            <span></span>
            <span></span>
            <span></span>
        </button>

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

    // Add sidebar toggle functionality
    const sidebarToggleBtn = navbar.querySelector("#sidebarToggle");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            sidebarToggleBtn.classList.toggle("active");
        });

        // Close sidebar when clicking on a menu item
        sidebar.querySelectorAll(".sidebar-link").forEach(link => {
            link.addEventListener("click", () => {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove("open");
                    sidebarToggleBtn.classList.remove("active");
                }
            });
        });

        // Close sidebar when clicking outside
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                !sidebarToggleBtn.contains(e.target)) {
                sidebar.classList.remove("open");
                sidebarToggleBtn.classList.remove("active");
            }
        });
    }
}