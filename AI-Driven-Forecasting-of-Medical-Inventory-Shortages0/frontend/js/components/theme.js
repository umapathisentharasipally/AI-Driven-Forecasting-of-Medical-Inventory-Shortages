const THEME_KEY = "med_theme";

export function applySavedTheme() {
  const savedTheme =
    localStorage.getItem(THEME_KEY) || "dark";

  document.documentElement.dataset.theme = savedTheme;

  document.documentElement.classList.toggle(
    "dark",
    savedTheme === "dark"
  );
}

export function toggleTheme() {
  const current =
    document.documentElement.dataset.theme || "dark";

  const next =
    current === "dark" ? "light" : "dark";

  localStorage.setItem(THEME_KEY, next);

  document.documentElement.dataset.theme = next;

  document.documentElement.classList.toggle(
    "dark",
    next === "dark"
  );

  return next;
}