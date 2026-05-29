const SENSITIVE_PATTERNS = [
  /OPENAI_API_KEY/i,
  /\bsk-[A-Za-z0-9]{8,}\b/,
  /\bbearer\s+[A-Za-z0-9\-\._~+/=]{8,}\b/i,
  /\bpassword\b/i,
  /\bsecret\b/i,
  /\bapi_key\b/i,
  /\.env/i,
];

const SAFE_VALUE_KEYS = new Set([
  "token_usage",
  "token_summary",
  "cost_usage",
  "cost_summary",
  "provider",
  "model",
  "input_tokens",
  "output_tokens",
  "cached_input_tokens",
  "total_tokens",
  "estimated",
  "estimated_tokens",
  "estimated_cost",
  "pricing_found",
  "input_cost",
  "output_cost",
  "cached_input_cost",
  "total_cost",
  "currency",
  "markdown",
  "markdown_report",
  "report",
  "content",
  "summary",
]);

function redactPath(value: string): string {
  const normalized = value.replace(/\\/g, "/");
  const parts = normalized.split("/").filter(Boolean);
  return parts[parts.length - 1] || "[path]";
}

export function sanitizeValue(value: unknown, key = ""): unknown {
  const loweredKey = key.toLowerCase();
  if (typeof value === "string") {
    if (SENSITIVE_PATTERNS.some((pattern) => pattern.test(value))) {
      return "[redacted]";
    }
    if (/^[A-Za-z]:[\\/]/.test(value) || value.startsWith("/")) {
      return redactPath(value);
    }
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean" || value === null) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item, key));
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const cleaned: Record<string, unknown> = {};
    for (const [itemKey, itemValue] of Object.entries(record)) {
      const lowered = itemKey.toLowerCase();
      if (SAFE_VALUE_KEYS.has(lowered)) {
        cleaned[itemKey] = sanitizeValue(itemValue, itemKey);
        continue;
      }
      if (SENSITIVE_PATTERNS.some((pattern) => pattern.test(itemKey))) {
        cleaned[itemKey] = "[redacted]";
        continue;
      }
      cleaned[itemKey] = sanitizeValue(itemValue, itemKey);
    }
    return cleaned;
  }
  return value;
}

export function sanitizeObject<T>(value: T): T {
  return sanitizeValue(value) as T;
}

export function safeJsonStringify(value: unknown, space = 2): string {
  const seen = new WeakSet<object>();
  return JSON.stringify(
    sanitizeValue(value),
    (_key, current) => {
      if (current && typeof current === "object") {
        if (seen.has(current)) {
          return "[circular]";
        }
        seen.add(current);
      }
      return current;
    },
    space,
  ) ?? "";
}
