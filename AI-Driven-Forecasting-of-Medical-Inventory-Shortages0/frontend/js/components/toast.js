export function showToast(message, type = "info") {
  const root =
    document.getElementById("toast-root") ||
    createToastRoot();

  while (root.children.length >= 3) {
    root.firstElementChild.remove();
  }

  const toast = document.createElement("div");

  toast.className = `
    toast toast-${type}
  `;

  toast.innerHTML = `
    <span>${message}</span>
    <button aria-label="Close notification">×</button>
  `;

  toast.querySelector("button").addEventListener("click", () => {
    toast.remove();
  });

  root.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("toast-hide");

    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

function createToastRoot() {
  const root = document.createElement("div");
  root.id = "toast-root";
  root.className = "toast-root";
  document.body.appendChild(root);
  return root;
}