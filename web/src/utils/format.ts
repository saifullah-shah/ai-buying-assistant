/** Presentation helpers. All currency is PKR per D-007 (provisional). */

const PKR = new Intl.NumberFormat("en-PK", {
  style: "currency",
  currency: "PKR",
  maximumFractionDigits: 0,
});

/**
 * Format a price. The curated dataset stores whole rupees, so we never show
 * fractional rupees or paisa.
 */
export function formatPrice(amount: number, currency = "PKR"): string {
  if (!Number.isFinite(amount)) return "—";
  if (currency === "PKR") return PKR.format(amount);
  return `${currency} ${Math.round(amount).toLocaleString("en-PK")}`;
}

/** Compact price for tight spaces, e.g. "Rs 265k". */
export function formatPriceCompact(amount: number): string {
  if (!Number.isFinite(amount)) return "—";
  if (amount >= 1000) return `Rs ${Math.round(amount / 1000)}k`;
  return `Rs ${amount}`;
}

export function formatNumber(value: unknown, unit?: string | null): string {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "number") {
    const shown = Number.isInteger(value) ? String(value) : value.toFixed(2);
    return unit ? `${shown} ${unit}` : shown;
  }
  return unit ? `${value} ${unit}` : String(value);
}

/** Format an ISO timestamp for display, e.g. "13 Oct 2026, 18:01". */
export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export const FRESHNESS_LABEL: Record<string, string> = {
  fresh: "Recently observed",
  stale: "May be out of date",
  unknown: "Observation time unknown",
};

export const CONDITION_LABEL: Record<string, string> = {
  new: "New",
  refurbished: "Refurbished",
  used: "Used",
  "open-box": "Open box",
  unknown: "Condition unknown",
};

/** Split a product name into a brand-ish prefix and the model, when possible. */
export function splitName(name: string): { head: string; tail: string } {
  const parts = name.trim().split(/\s+/);
  if (parts.length <= 1) return { head: name, tail: "" };
  // "DemoWorks Study 14 A" -> head "DemoWorks", tail "Study 14 A"
  return { head: parts[0], tail: parts.slice(1).join(" ") };
}

/** Deterministic 0..n-1 index from a string, used for the generated visuals. */
export function hashIndex(seed: string, buckets: number): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash) % buckets;
}

export const PKR_BUDGET_SHORTCUTS = [
  { label: "Under Rs 100,000", value: 100000 },
  { label: "Under Rs 150,000", value: 150000 },
  { label: "Under Rs 200,000", value: 200000 },
  { label: "Under Rs 300,000", value: 300000 },
];