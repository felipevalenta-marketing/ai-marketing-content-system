export function toTitleCase(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatCount(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0";
  }
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatCurrency(value: unknown, currency = "USD"): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return `${currency} 0.000000`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 6,
  }).format(value);
}

export function formatPercent(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0.00%";
  }
  return `${value.toFixed(2)}%`;
}

export function formatStatusTone(status?: string): "ok" | "warn" | "error" | "neutral" {
  const normalized = (status ?? "").toLowerCase();
  if (["ok", "healthy", "success", "completed", "approved", "persisted"].includes(normalized)) {
    return "ok";
  }
  if (["warning", "warnings", "partial", "requires_approval", "dry_run"].includes(normalized)) {
    return "warn";
  }
  if (["error", "failed", "rejected"].includes(normalized)) {
    return "error";
  }
  return "neutral";
}

export function getRoleTone(role?: string): "success" | "warning" | "error" | "neutral" {
  const normalized = (role ?? "").toLowerCase();
  if (normalized === "admin") {
    return "success";
  }
  if (normalized === "manager") {
    return "warning";
  }
  if (normalized === "disabled") {
    return "error";
  }
  return "neutral";
}

export function getRoleLabel(role?: string): string {
  if (!role) {
    return "Viewer";
  }
  return toTitleCase(role.replace(/[-_]+/g, " "));
}

export function getStatusLabel(value?: string): string {
  if (!value) {
    return "Unknown";
  }
  return toTitleCase(value.replace(/[-_]+/g, " "));
}

export function extractMarkdown(value: unknown): string {
  if (!value || typeof value !== "object") {
    return "";
  }
  const record = value as Record<string, unknown>;
  const candidates = ["markdown", "markdown_report", "rendered_markdown", "content", "text"];
  for (const key of candidates) {
    if (typeof record[key] === "string" && String(record[key]).trim()) {
      return String(record[key]);
    }
    if (record[key] && typeof record[key] === "object") {
      const nested = extractMarkdown(record[key]);
      if (nested) {
        return nested;
      }
    }
  }
  return "";
}

export function joinList(items?: string[] | null, separator = ", "): string {
  if (!items || items.length === 0) {
    return "None";
  }
  return items.join(separator);
}

export function formatMaybeString(value: unknown, fallback = "-"): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return fallback;
}
