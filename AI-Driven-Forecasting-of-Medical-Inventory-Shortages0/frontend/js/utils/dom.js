export function $(selector, parent = document) {
  return parent.querySelector(selector);
}

export function $all(selector, parent = document) {
  return Array.from(parent.querySelectorAll(selector));
}

export function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}