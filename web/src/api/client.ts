/**
 * Typed HTTP client for the Python API.
 *
 * Every request goes to a real endpoint on `aba.api.app`. There are no mock
 * responses, no fabricated product data and no client-side "fake AI" replies in
 * this module — if the backend is down the caller gets a thrown ApiError and
 * the UI renders a real error state.
 */
import type {
  AssistantResponse,
  CompareResponse,
  Condition,
  DatasetResponse,
  DiscoverResponse,
  HealthResponse,
  ProductDetailResponse,
  SortKey,
} from "./types";

const BASE = "/api";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(message: string, status: number, detail = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(
      "Could not reach the buying assistant API. Is the backend running on port 8000?",
      0,
      cause instanceof Error ? cause.message : String(cause),
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg) detail = body.detail[0].msg;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      `Request failed (${response.status})`,
      response.status,
      detail,
    );
  }

  return (await response.json()) as T;
}

export interface DiscoverParams {
  q?: string;
  budget?: number;
  currency?: string;
  condition?: Condition | null;
  mustHave?: string[];
  niceToHave?: string[];
  minRam?: number;
  minStorage?: number;
  maxWeight?: number;
  minScreen?: number;
  sort?: SortKey;
}

export function buildDiscoverQuery(params: DiscoverParams): string {
  const qs = new URLSearchParams();
  if (params.q?.trim()) qs.set("q", params.q.trim());
  if (typeof params.budget === "number" && Number.isFinite(params.budget) && params.budget > 0) {
    qs.set("budget", String(Math.round(params.budget)));
  }
  if (params.currency) qs.set("currency", params.currency);
  if (params.condition) qs.set("condition", params.condition);
  for (const key of params.mustHave ?? []) qs.append("must_have", key);
  for (const key of params.niceToHave ?? []) qs.append("nice_to_have", key);
  if (typeof params.minRam === "number") qs.set("min_ram", String(params.minRam));
  if (typeof params.minStorage === "number") qs.set("min_storage", String(params.minStorage));
  if (typeof params.maxWeight === "number") qs.set("max_weight", String(params.maxWeight));
  if (typeof params.minScreen === "number") qs.set("min_screen", String(params.minScreen));
  if (params.sort && params.sort !== "relevance") qs.set("sort", params.sort);
  return qs.toString();
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  dataset: () => request<DatasetResponse>("/dataset"),

  discover: (params: DiscoverParams, signal?: AbortSignal) => {
    const qs = buildDiscoverQuery(params);
    return request<DiscoverResponse>(`/products${qs ? `?${qs}` : ""}`, { signal });
  },

  product: (id: string, signal?: AbortSignal) =>
    request<ProductDetailResponse>(`/products/${encodeURIComponent(id)}`, { signal }),

  compare: (productIds: string[]) =>
    request<CompareResponse>("/compare", {
      method: "POST",
      body: JSON.stringify({ product_ids: productIds }),
    }),

  assistant: (body: {
    query?: string | null;
    budget_amount?: number | null;
    budget_currency?: string;
    product_ids?: string[];
    sort?: SortKey;
  }) =>
    request<AssistantResponse>("/assistant", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};