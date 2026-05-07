export function formatDate(value?: string | null) {
  if (!value) return "No deadline";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatScore(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return "0%";
  return `${Math.round(value * 100)}%`;
}

export function isOverdue(value?: string | null) {
  return Boolean(value && new Date(value).getTime() < Date.now());
}
