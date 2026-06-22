export function initGlobalSearch() {
  const input = document.getElementById("globalSearch");

  if (!input) return;

  document.addEventListener("keydown", event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      input.focus();
    }
  });

  input.addEventListener("input", event => {
    const value = event.target.value.trim();

    if (value.length < 2) return;

    document.dispatchEvent(
      new CustomEvent("medinv:global-search", {
        detail: { query: value }
      })
    );
  });
}