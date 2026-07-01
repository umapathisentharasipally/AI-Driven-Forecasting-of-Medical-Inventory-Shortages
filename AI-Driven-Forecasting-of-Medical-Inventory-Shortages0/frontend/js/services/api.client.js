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
  // Clear all token variations
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("med_user");
  
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
  sessionStorage.removeItem("token");

  // Redirect to login
  console.warn("Session expired. Redirecting to login...");
  
  // Use hash-based navigation for SPA
  if (window.location.hash !== "#login") {
    window.location.hash = "#login";
    window.location.reload();
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
    console.error("❌ Unauthorized: Token missing, invalid, or expired.");
    redirectToLogin();
    throw new Error("Unauthorized - Session expired. Please login again.");
  }

  if (!response.ok) {
    console.error("❌ API ERROR:", {
      status: response.status,
      endpoint: endpoint,
      error: data?.error?.message || data?.message || "Unknown error"
    });
    throw new Error(data?.error?.message || data?.message || `Request failed with status ${response.status}`);
  }

  return data;
}