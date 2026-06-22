export function showToast(message, type = "success") {
  const root = document.getElementById("toast-root");

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  root.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}