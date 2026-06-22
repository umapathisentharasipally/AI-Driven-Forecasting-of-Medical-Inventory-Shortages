const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function getAccessToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token")
  );
}

function redirectToLogin() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("token");
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
  sessionStorage.removeItem("token");

  if (!window.location.pathname.includes("login")) {
    window.location.href = "/login.html";
  }
}

export async function apiRequest(endpoint, options = {}) {
  const token = getAccessToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (response.status === 401) {
    console.error("Unauthorized. Token missing or expired.");
    redirectToLogin();
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    console.error("API ERROR:", data);
    throw new Error(data?.error?.message || `Request failed with status ${response.status}`);
  }

  return data;
}