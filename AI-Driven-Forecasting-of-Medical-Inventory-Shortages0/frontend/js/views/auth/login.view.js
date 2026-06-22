import { authService } from "../../services/auth.service.js";
import { saveSession, isAuthenticated, redirectToApp, redirectByRole } from "../../auth/session.js";

const app = document.getElementById("app");

export function renderLogin() {
  if (isAuthenticated()) {
    redirectToApp();
    return;
  }

  document.body.classList.add("login-body");

  app.innerHTML = `
    <main class="login-page">
      <section class="login-shell">

        <aside class="login-brand-panel">
          <div class="brand-content">
            <div class="brand-logo-row">
              <div class="brand-shield">✚</div>
              <div>
                <h1>MedInv <span>Forecast</span></h1>
                <p>Medical Inventory Forecasting System</p>
              </div>
            </div>

            <div class="brand-hero">
              <h2>Smarter Inventory.<br><span>Better Healthcare.</span></h2>
              <p>
                AI-powered insights and analytics to optimize medical inventory,
                reduce stockouts, and improve patient care.
              </p>
            </div>

            <div class="feature-list">
              ${feature("📈", "AI-Powered Forecasting", "Accurate demand predictions to prevent stockouts and overstocking.")}
              ${feature("🛡️", "Real-time Monitoring", "Track inventory, alerts, and system health in real time.")}
              ${feature("🔔", "Smart Alerts", "Get notified about risks, expiries, and critical stock levels.")}
              ${feature("◔", "Data-Driven Decisions", "Comprehensive analytics and reports to support better decisions.")}
            </div>

            <div class="trust-card">
              <div class="trust-icon">🏥</div>
              <div>
                <h3>Trusted by 500+ hospitals</h3>
                <p>to streamline their inventory operations.</p>
              </div>
            </div>
          </div>
        </aside>

        <section class="login-form-panel">
          <div class="theme-switcher">
            <button id="lightThemeBtn" type="button">☼</button>
            <button id="darkThemeBtn" type="button">☾</button>
          </div>

          <div class="form-wrapper">
            <header class="form-header">
              <h2>Welcome Back!</h2>
              <p>Sign in to access your dashboard</p>
            </header>

            <form id="loginForm" class="login-form" novalidate>
              <div class="form-group">
                <label for="username">Email</label>
                <div class="input-wrapper">
                  <span class="input-icon">👤</span>
                  <input id="username" name="email" type="email" placeholder="Enter your email" autocomplete="email"/>
                </div>
                <small id="usernameError" class="field-error"></small>
              </div>

              <div class="form-group">
                <label for="password">Password</label>
                <div class="input-wrapper">
                  <span class="input-icon">🔒</span>
                  <input id="password" name="password" type="password" placeholder="Enter your password" autocomplete="current-password">
                  <button id="togglePasswordBtn" class="password-toggle" type="button">👁</button>
                </div>
                <small id="passwordError" class="field-error"></small>
              </div>

              <div class="form-meta">
                <span></span>
                <button id="forgotPasswordBtn" type="button">Forgot Password?</button>
              </div>

              <button id="loginSubmitBtn" class="login-submit" type="submit">
                <span class="btn-text">Sign In</span>
                <span class="btn-arrow">→</span>
                <span class="btn-loader" hidden></span>
              </button>

              <div id="formError" class="form-error"></div>
            </form>

            <section class="secure-info">
              <div class="secure-line"><span></span><strong>🛡</strong><span></span></div>
              <h3>Secure & Role-Based Access</h3>
              <p>Your dashboard will be personalized based on your role and permissions.</p>
            </section>
          </div>

          <footer class="login-security-footer">
            <span>🛡 Secure Login</span>
            <i></i>
            <span>🔒 Role-Based Access</span>
            <i></i>
            <span>👥 Protected Data</span>
          </footer>
        </section>
      </section>

      <footer class="copyright-footer">
        <span>© 2025 MedInv Forecast. All rights reserved.</span>
        <i></i>
        <a href="#">Privacy Policy</a>
        <i></i>
        <a href="#">Terms of Service</a>
      </footer>
    </main>
  `;

  bindLoginEvents();
}

function feature(icon, title, text) {
  return `
    <article class="feature-item">
      <div class="feature-icon">${icon}</div>
      <div>
        <h3>${title}</h3>
        <p>${text}</p>
      </div>
    </article>
  `;
}

function bindLoginEvents() {
  const form = document.getElementById("loginForm");
  const username = document.getElementById("username");
  const password = document.getElementById("password");
  const submitBtn = document.getElementById("loginSubmitBtn");
  const btnText = submitBtn.querySelector(".btn-text");
  const btnArrow = submitBtn.querySelector(".btn-arrow");
  const btnLoader = submitBtn.querySelector(".btn-loader");

  username.focus();

  document.getElementById("togglePasswordBtn").addEventListener("click", () => {
    password.type = password.type === "password" ? "text" : "password";
  });

  document.getElementById("lightThemeBtn").addEventListener("click", () => setTheme("light"));
  document.getElementById("darkThemeBtn").addEventListener("click", () => setTheme("dark"));

  form.addEventListener("submit", async event => {
    event.preventDefault();

    clearErrors();

    const payload = {
      username: username.value.trim(),
      password: password.value
    };

    const errors = validateLogin(payload);

    if (Object.keys(errors).length) {
      showErrors(errors);
      return;
    }

    setLoading(true);

    try {
      const response = await authService.login(payload);

      if (!response.access_token || !response.refresh_token) {
        throw new Error("Invalid login response from server.");
      }

      saveSession(response);

      setTimeout(() => {
        redirectByRole(response.role);
      }, 300);

    } catch (error) {
      document.getElementById("formError").textContent =
        error?.message || "Login failed. Please try again.";
    } finally {
      setLoading(false);
    }
  });

  function setLoading(loading) {
    submitBtn.disabled = loading;
    username.disabled = loading;
    password.disabled = loading;
    btnText.textContent = loading ? "Signing In" : "Sign In";
    btnArrow.hidden = loading;
    btnLoader.hidden = !loading;
  }
}

function validateLogin(data) {
  const errors = {};

  if (!data.username) {
    errors.username = "Username is required";
  }

  if (!data.password) {
    errors.password = "Password is required";
  } else if (data.password.length < 8) {
    errors.password = "Password must be at least 8 characters";
  } else if (data.password.length > 14) {
    errors.password = "Password cannot exceed 14 characters";
  }

  return errors;
}

function showErrors(errors) {
  if (errors.username) document.getElementById("usernameError").textContent = errors.username;
  if (errors.password) document.getElementById("passwordError").textContent = errors.password;
}

function clearErrors() {
  document.getElementById("usernameError").textContent = "";
  document.getElementById("passwordError").textContent = "";
  document.getElementById("formError").textContent = "";
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("med_theme", theme);
}