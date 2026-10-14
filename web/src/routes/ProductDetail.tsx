import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ProductDetailResponse } from "../api/types";
import { ProductVisual } from "../components/ProductVisual";
import { SpecTable } from "../components/SpecTable";
import { DemoNotice } from "../components/Layout";
import { useSession } from "../state/SessionContext";
import {
  CONDITION_LABEL,
  FRESHNESS_LABEL,
  formatDateTime,
  formatNumber,
  formatPrice,
} from "../utils/format";

export default function ProductDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { toggleCompare, isComparing, compareFull, toggleSaved, isSaved } = useSession();
  const [data, setData] = useState<ProductDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(null);

    api
      .product(id, controller.signal)
      .then(setData)
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? err.status === 404
              ? "That product is not in the demonstration catalogue."
              : err.message
            : "Could not load this product.",
        );
      })
      .finally(() => !controller.signal.aborted && setLoading(false));

    return () => controller.abort();
  }, [id]);

  if (loading) {
    return (
      <div className="shell page">
        <div className="skeleton" style={{ height: 28, width: "38%", marginBottom: 24 }} />
        <div className="detail-layout">
          <div className="skeleton" style={{ aspectRatio: "16/10", borderRadius: 10 }} />
          <div>
            <div className="skeleton" style={{ height: 22, marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 14, width: "70%", marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 44, marginTop: 20 }} />
          </div>
        </div>
        <span className="sr-only" role="status">
          Loading product
        </span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="shell page">
        <div className="state state--error" role="alert">
          <p className="state__title">Product unavailable</p>
          <p className="state__body">{error}</p>
          <button type="button" className="btn btn--primary btn--sm" onClick={() => navigate("/discover")}>
            Back to discovery
          </button>
        </div>
      </div>
    );
  }

  const { product, offers, unknown_fields: unknownFields, meta } = data;
  const offer = offers[0] ?? null;
  const comparing = isComparing(product.product_id);
  const saved = isSaved(product.product_id);
  const known = product.specs.filter((s) => !s.is_unknown);

  // Deterministic, record-grounded observations. No LLM, no invented claims.
  const observations: string[] = [];
  const ram = product.specs.find((s) => s.key === "ram_gb");
  const storage = product.specs.find((s) => s.key === "storage_gb");
  const weight = product.specs.find((s) => s.key === "weight_kg");
  const gpu = product.specs.find((s) => s.key === "gpu");
  const screen = product.specs.find((s) => s.key === "screen_size_in");

  if (ram && !ram.is_unknown && typeof ram.value === "number" && ram.value >= 16) {
    observations.push(`${ram.value} GB of memory suits heavier multitasking and most programming work.`);
  }
  if (storage && !storage.is_unknown && typeof storage.value === "number" && storage.value >= 512) {
    observations.push(`${storage.value} GB of storage leaves room for large project files without immediate upgrade.`);
  }
  if (weight && !weight.is_unknown && typeof weight.value === "number" && weight.value <= 1.5) {
    observations.push(`At ${weight.value} kg it is in the lighter range, easier to carry between classes or offices.`);
  }
  if (screen && !screen.is_unknown && typeof screen.value === "number" && screen.value <= 13.5) {
    observations.push(`A ${screen.value}-inch screen keeps the footprint small for travel.`);
  }
  if (gpu && !gpu.is_unknown && /dedicated/i.test(String(gpu.value))) {
    observations.push("The record lists a dedicated GPU, which matters for graphics-heavy workloads.");
  } else if (gpu && !gpu.is_unknown && /integrated/i.test(String(gpu.value))) {
    observations.push("Graphics are integrated, so heavy 3D or gaming workloads are not the target.");
  }
  if (unknownFields.length > 0) {
    observations.push(
      `${unknownFields.join(" and ")} ${unknownFields.length === 1 ? "is" : "are"} not disclosed in the source record, so no claim can be made about ${unknownFields.length === 1 ? "it" : "them"}.`,
    );
  }

  return (
    <div className="shell page">
      <nav aria-label="Breadcrumb" className="small" style={{ marginBottom: "var(--space-5)" }}>
        <Link to="/discover" style={{ textDecoration: "none" }}>
          ← Back to results
        </Link>
        <span className="muted"> (your search is preserved)</span>
      </nav>

      <div className="detail-layout">
        {/* ---------- Left column ---------- */}
        <div className="stack" style={{ ["--flow" as string]: "var(--space-6)" }}>
          <ProductVisual
            productId={product.product_id}
            name={product.name}
            specs={product.specs}
            variant="hero"
          />

          <section aria-labelledby="specs-heading" className="card card--pad">
            <div className="section-head" style={{ marginBottom: "var(--space-4)" }}>
              <div>
                <p className="eyebrow" style={{ marginBottom: "var(--space-1)" }}>
                  Recorded specifications
                </p>
                <h2 id="specs-heading" style={{ fontSize: "var(--text-lg)" }}>
                  What the source actually says
                </h2>
              </div>
            </div>
            <SpecTable specs={product.specs} caption={`Source: ${meta.dataset_id} (synthetic fixture, checked ${formatDateTime(meta.created_at_utc)} UTC)`} />
          </section>

          {observations.length > 0 ? (
            <section aria-labelledby="obs-heading" className="card card--pad">
              <p className="eyebrow" style={{ marginBottom: "var(--space-3)" }}>
                Trade-offs
              </p>
              <h2 id="obs-heading" style={{ fontSize: "var(--text-lg)", marginBottom: "var(--space-3)" }}>
                What this record supports
              </h2>
              <ul className="stack" style={{ ["--flow" as string]: "var(--space-3)" }}>
                {observations.map((line) => (
                  <li key={line} className="small" style={{ display: "flex", gap: "var(--space-3)" }}>
                    <span aria-hidden="true" style={{ color: "var(--accent)" }}>—</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
              <p className="xsmall muted" style={{ marginTop: "var(--space-4)" }}>
                These observations are derived directly from the values above by rule. They are not
                manufacturer claims and not an opinion from a language model.
              </p>
            </section>
          ) : null}
        </div>

        {/* ---------- Right column ---------- */}
        <aside className="stack" style={{ ["--flow" as string]: "var(--space-5)" }}>
          <div className="card card--pad">
            <p className="eyebrow" style={{ marginBottom: "var(--space-2)" }}>
              {product.category} · {product.market}
            </p>
            <h1 style={{ fontSize: "var(--text-2xl)", marginBottom: "var(--space-4)" }}>
              {product.name}
            </h1>

            {offer ? (
              <>
                <p className="price" style={{ fontSize: "var(--text-2xl)", fontFamily: "var(--font-display)" }}>
                  {formatPrice(offer.price_amount)}
                </p>
                <div className="cluster" style={{ ["--cluster-gap" as string]: "6px", marginTop: "var(--space-3)" }}>
                  <span className="badge">{CONDITION_LABEL[offer.condition] ?? offer.condition}</span>
                  <span className={`badge badge--${offer.freshness === "fresh" ? "ok" : "warn"}`}>
                    <span className="badge__dot" aria-hidden="true" />
                    {FRESHNESS_LABEL[offer.freshness]}
                  </span>
                  <span className="badge">Synthetic seller</span>
                </div>

                <dl className="small" style={{ ["--flow" as string]: "var(--space-2)", marginTop: "var(--space-4)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-3)" }}>
                    <dt className="muted">Seller record</dt>
                    <dd style={{ margin: 0 }}>{offer.seller_id}</dd>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-3)" }}>
                    <dt className="muted">Price observed</dt>
                    <dd style={{ margin: 0 }}>{formatDateTime(offer.observed_at)}</dd>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-3)" }}>
                    <dt className="muted">Availability</dt>
                    <dd style={{ margin: 0, color: "var(--warn)" }}>Unknown</dd>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-3)" }}>
                    <dt className="muted">Source</dt>
                    <dd style={{ margin: 0 }} className="mono xsmall">{offer.source_id}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="muted small">No seller offer is recorded for this product.</p>
            )}

            <div className="stack" style={{ ["--flow" as string]: "var(--space-3)", marginTop: "var(--space-5)" }}>
              <button
                type="button"
                className="btn btn--primary btn--block"
                onClick={() => toggleCompare(product.product_id, product.name)}
                disabled={!comparing && compareFull}
                aria-pressed={comparing}
              >
                {comparing ? "✓ In comparison" : "+ Add to comparison"}
              </button>
              <button
                type="button"
                className="btn btn--secondary btn--block"
                onClick={() => toggleSaved(product.product_id, product.name)}
                aria-pressed={saved}
              >
                {saved ? "★ Saved" : "☆ Save to shortlist"}
              </button>
              {comparing ? (
                <Link to="/compare" className="btn btn--ghost btn--sm btn--block">
                  Open comparison studio
                </Link>
              ) : null}
            </div>

            <p className="xsmall muted" style={{ marginTop: "var(--space-4)" }}>
              This assistant does not sell anything. There is no checkout, no payment and no
              stock guarantee — the record above is illustrative.
            </p>
          </div>

          <DemoNotice notice={meta.important_notice} />

          {unknownFields.length > 0 ? (
            <div className="card card--pad">
              <p className="eyebrow" style={{ marginBottom: "var(--space-2)" }}>
                Gaps in the record
              </p>
              <h2 style={{ fontSize: "var(--text-md)", marginBottom: "var(--space-3)" }}>
                {unknownFields.length} unknown{" "}
                {unknownFields.length === 1 ? "field" : "fields"}
              </h2>
              <p className="xsmall muted" style={{ marginBottom: "var(--space-3)" }}>
                These are genuinely missing from the source. The assistant will not estimate them.
              </p>
              <ul className="stack" style={{ ["--flow" as string]: "6px" }}>
                {unknownFields.map((field) => (
                  <li key={field} className="small">
                    <span className="badge badge--warn">{field}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {known.length > 0 ? (
            <div className="card card--pad">
              <p className="eyebrow" style={{ marginBottom: "var(--space-3)" }}>
                At a glance
              </p>
              <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
                {known.slice(0, 6).map((spec) => (
                  <span className="spec-pill" key={spec.key}>
                    <span className="spec-pill__k">{spec.label}</span>
                    <span className="spec-pill__v">{formatNumber(spec.value, spec.unit)}</span>
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}