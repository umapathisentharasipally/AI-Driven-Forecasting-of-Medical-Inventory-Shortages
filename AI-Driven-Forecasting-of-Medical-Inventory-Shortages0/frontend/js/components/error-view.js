export function renderErrorView(message = "Something went wrong") {
  const app = document.getElementById("app");

  app.innerHTML = `
    <main class="error-page">
      <section class="error-card">
        <div class="error-icon">⚠️</div>

        <h1>Unable to Load Page</h1>

        <p>${message}</p>

        <button data-nav="dashboard" class="primary-btn">
          Go to Dashboard
        </button>
      </section>
    </main>
  `;
}

export function renderNotFoundView() {
  const app = document.getElementById("app");

  app.innerHTML = `
    <main class="error-page">
      <section class="error-card">
        <div class="error-icon">404</div>

        <h1>Page Not Found</h1>

        <p>The requested module does not exist.</p>

        <button data-nav="dashboard" class="primary-btn">
          Back to Dashboard
        </button>
      </section>
    </main>
  `;
}