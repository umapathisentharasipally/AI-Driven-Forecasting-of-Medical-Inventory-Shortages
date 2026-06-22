export function formatDate(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

export function formatDateTime(value) {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function toInputDate(value) {
  if (!value) return "";

  return new Date(value).toISOString().slice(0, 10);
}

export function getCurrentWeekRange() {
  const today = new Date();
  const end = new Date(today);
  const start = new Date(today);

  start.setDate(today.getDate() - 6);

  return {
    start_date: toInputDate(start),
    end_date: toInputDate(end),
    label: `${formatDate(start)} – ${formatDate(end)}`
  };
}

export function getPreviousDaysRange(days = 7) {
  const today = new Date();
  const start = new Date(today);

  start.setDate(today.getDate() - Number(days));

  return {
    start_date: toInputDate(start),
    end_date: toInputDate(today),
    label: `${formatDate(start)} – ${formatDate(today)}`
  };
}

export function timeAgo(value) {
  if (!value) return "-";

  const date = new Date(value);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return "Just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days > 1 ? "s" : ""} ago`;

  return formatDate(value);
}