/**
 * TypeScript mirror of the Python API contract (aba/api).
 *
 * These types are hand-written to match `aba/api/dataset.py::product_view`,
 * `offer_view` and `aba/api/service.py::discover`. They are the single source
 * of truth on the frontend for what the backend actually returns.
 */

export interface EvidenceView {
  provider: string;
  source_id: string | null;
  note: string;
}

export interface SpecView {
  key: string;
  label: string;
  value: string | number | null;
  unit: string | null;
  is_unknown: boolean;
  evidence: EvidenceView;
}

export interface ProductView {
  product_id: string;
  name: string;
  category: string;
  market: string;
  is_demo: boolean;
  specs: SpecView[];
}

export type Freshness = "fresh" | "stale" | "unknown";

export interface OfferView {
  product_id: string;
  seller_id: string;
  price_amount: number;
  price_currency: string;
  /** The curated dataset stores whole rupees, stated explicitly. */
  currency_unit: string;
  condition: string;
  product_url: string;
  observed_at: string;
  freshness: Freshness;
  source_id: string;
  is_demo: boolean;
}

export interface MatchesView {
  budget: boolean;
  condition: boolean;
  must_haves: boolean;
  filters_ok: boolean;
  nice_to_haves_score: number;
  nice_to_haves_total: number;
}

export interface ReasonsView {
  budget: string;
  condition: string;
  must_haves: string;
  filters: string[];
}

export interface ResultView {
  product: ProductView;
  offer: OfferView;
  matches: MatchesView;
  reasons: ReasonsView;
  failed_constraints?: string[];
}

export interface DatasetMeta {
  dataset_id: string;
  dataset_status: string;
  market: string;
  category: string;
  created_at_utc: string;
  is_demo: boolean;
  important_notice: string;
  evidence: Array<{
    evidence_id: string;
    source_type: string;
    source_name: string;
    source_url: string | null;
    checked_at_utc: string;
    supports: string;
    is_demo: boolean;
  }>;
}

export interface DiscoverResponse {
  meta: DatasetMeta;
  query: string | null;
  budget_amount: number | null;
  budget_currency: string;
  condition: string | null;
  sort: string;
  total_matched: number;
  total_considered: number;
  results: ResultView[];
  rejected: ResultView[];
  notes: string[];
  hints: { suggested_nice_to_haves: string[] };
  validation: { is_valid: boolean; errors: string[] };
}

export interface ProductDetailResponse {
  product: ProductView;
  offers: OfferView[];
  meta: DatasetMeta;
  unknown_fields: string[];
  unknown_field_keys: string[];
}

export interface CompareCell {
  value: string | number | null;
  is_unknown: boolean;
  display: string;
}

export interface CompareRow {
  key: string;
  label: string;
  cells: CompareCell[];
}

export interface CompareResponse {
  meta: DatasetMeta;
  products: Array<{
    product: ProductView;
    offer: OfferView | null;
    offer_count: number;
  }>;
  rows: CompareRow[];
}

export type AssistantMode = "live" | "demo" | "none";

export interface Explanation {
  index: number;
  product_id: string;
  product_name: string;
  fits_because: string;
  what_it_sacrifices: string;
  unknown_and_why: string[];
  constraint_summary: string;
  evidence?: string;
}

export interface AssistantResponse {
  mode: AssistantMode;
  notice: string;
  explanations: Explanation[];
  model: string | null;
  raw_response: string | null;
  validated: boolean;
  shortlist_size?: number;
}

export interface HealthResponse {
  status: string;
  service: string;
  llm: {
    api_key_present: boolean;
    model: string | null;
    mode_if_used: "live" | "demo";
  };
}

export interface DatasetResponse {
  meta: DatasetMeta;
  product_count: number;
  offer_count: number;
}

export type Condition = "new" | "refurbished" | "used" | "open-box";

export type SortKey =
  | "relevance"
  | "price_asc"
  | "price_desc"
  | "ram_desc"
  | "screen_desc"
  | "weight_asc";

export const SORT_LABELS: Record<SortKey, string> = {
  relevance: "Best match",
  price_asc: "Price: low to high",
  price_desc: "Price: high to low",
  ram_desc: "Most memory",
  screen_desc: "Largest screen",
  weight_asc: "Lightest first",
};

export const CONDITIONS: Condition[] = ["new", "refurbished", "used", "open-box"];

/** Spec keys that can be used as hard must-haves or soft nice-to-haves. */
export interface SpecOption {
  key: string;
  label: string;
}

export const MUST_HAVE_OPTIONS: SpecOption[] = [
  { key: "ram_gb", label: "Memory (RAM)" },
  { key: "storage_gb", label: "Storage capacity" },
  { key: "screen_size_in", label: "Screen size" },
  { key: "weight_kg", label: "Weight" },
  { key: "gpu", label: "Graphics (GPU)" },
  { key: "cpu", label: "Processor (CPU)" },
];

export const NICE_TO_HAVE_OPTIONS: SpecOption[] = [
  { key: "ram_gb", label: "Memory (RAM)" },
  { key: "storage_gb", label: "Storage capacity" },
  { key: "screen_size_in", label: "Screen size" },
  { key: "weight_kg", label: "Lightweight" },
  { key: "gpu", label: "Graphics (GPU)" },
  { key: "cpu", label: "Processor (CPU)" },
  { key: "operating_system", label: "Operating system included" },
];