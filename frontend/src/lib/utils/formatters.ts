export function formatScore(score: number | null | undefined): string {
  if (score == null) return "--";
  return String(Math.round(score));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "--";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "--";
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function getScoreColor(score: number | null | undefined): string {
  if (score == null) return "var(--muted)";
  if (score >= 85) return "var(--green)";
  if (score >= 70) return "var(--accent)";
  if (score >= 50) return "var(--amber)";
  return "var(--danger)";
}
