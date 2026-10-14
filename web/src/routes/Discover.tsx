import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useDiscover } from "../hooks/useDiscover";
import { useCriteriaUrlSync } from "../hooks/useCriteriaUrlSync";
import { useSession } from "../state/SessionContext";
import { FilterPanel } from "../components/FilterPanel";
import { Drawer } from "../components/Overlays";
import { DemoNotice } from "../components/Layout";
import { ProductCard, ProductCardSkeleton } from "../components/ProductCard";
import { AssistantPanel } from "../components/AssistantPanel";
import { SORT_LABELS, type SortKey } from "../api/types";
import { formatPrice } from "../utils/format";

export default function Discover() {
  const { data, loading, error, retry } = useDiscover();
  const { criteria, setCriteria, resetCriteria, activeFilterCount } = useSession();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);

  // Keeps ?budget=… &condition=… in the URL so a search is shareable and
  // survives a refresh or a back/forward navigation.
  useCriteriaUrlSync();

  // Close the drawer if the viewport grows past the mobile breakpoint.
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const onChange = () => mq.matches && setDrawerOpen(false);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const chips = useMemo(() => {
    const list: Array<{ key: string; label: string; clear: () => void }> = [];
    if (criteria.budget !== null) {
      list.push({
        key: "budget",
        label: `Under ${formatPrice(criteria.budget)}`,
        clear: () => setCriteria({ budget: null }),
      });
    }
    if (criteria.condition) {
      list.push({
        key: "condition",
        label: `Condition: ${criteria.condition}`,
        clear: () => setCriteria({ condition: null }),
      });
    }
    criteria.mustHave.forEach((key) =>
      list.push({
        key: `must-${key}`,
        label: `Required: ${key.replace(/_/g, " ")}`,
        clear: () =>
          setCriteria({ mustHave: criteria.mustHave.filter((k) => k !== key) }),
      }),
    );
    criteria.niceToHave.forEach((key) =>
      list.push({
        key: `nth-${key}`,
        label: `Prefers: ${key.replace(/_/g, " ")}`,
        clear: () =>
          setCriteria({ niceToHave: criteria.niceToHave.filter((k) => k !== key) }),
      }),
    );
    if (criteria.minRam !== null)
      list.push({
        key: "minRam",
        label: `${criteria.minRam} GB+ memory`,
        clear: () => setCriteria({ minRam: null }),
      });
    if (criteria.minStorage !== null)
      list.push({
        key: "minStorage",
        label: `${criteria.minStorage} GB+ storage`,
        clear: () => setCriteria({ minStorage: null }),
      });
    if (criteria.minScreen !== null)
      list.push({
        key: "minScreen",
        label: `${criteria.minScreen}"+ screen`,
        clear: () => setCriteria({ minScreen: null }),
      });
    if (criteria.maxWeight !== null)
      list.push({
        key: "maxWeight",
        label: `Under ${criteria.maxWeight} kg`,
        clear: () => setCriteria({ maxWeight: null }),
      });
    return list;
  }, [criteria, setCriteria]);

  const heading = criteria.q?.trim() || (criteria.budget ? `Laptops under ${formatPrice(criteria.budget)}` : "All laptops on record");

  return (
    <div className="shell page">
      <div className="section-head">
        <div>
          <p className="eyebrow">Product discovery</p>
          <h1 style={{ fontSize: "var(--text-2xl)" }}>{heading}</h1>
          {data ? (
            <p className="muted small" style={{ marginTop: "var(--space-2)" }}>
              {data.total_matched} of {data.total_considered} demonstration{" "}
              {data.total_considered === 1 ? "record" : "records"} match your constraints
              {data.rejected.length > 0
                ? ` · ${data.rejected.length} excluded`
                : ""}
            </p>
          ) : null}
        </div>
        <div className="cluster">
          <button
            type="button"
            className="btn btn--secondary btn--sm"
            onClick={() => setAssistantOpen((v) => !v)}
            aria-expanded={assistantOpen}
            aria-controls="assistant-panel"
          >
            {assistantOpen ? "Hide assistant" : "Ask the assistant"}
          </button>
          <Link to="/compare" className="btn btn--secondary btn--sm">
            Comparison studio
          </Link>
        </div>
      </div>

      {/* Search context is preserved in the URL-less session store, so navigating
          into a product and back does not restart the search. */}
      <div className="field" style={{ marginBottom: "var(--space-5)", maxWidth: 620 }}>
        <label className="field__label" htmlFor="discover-query">
          Describe what you need
        </label>
        <input
          id="discover-query"
          className="input"
          type="text"
          value={criteria.q}
          placeholder="e.g. a laptop for programming and machine learning"
          autoComplete="off"
          onChange={(e) => setCriteria({ q: e.target.value })}
        />
        <span className="field__hint">
          This is used to suggest preferences you can confirm below. Hard constraints always come
          from the explicit filters, never from a guess about your sentence.
        </span>
      </div>

      {data?.hints.suggested_nice_to_haves.length ? (
        <div
          className="panel"
          style={{ marginBottom: "var(--space-5)", display: "flex", gap: "var(--space-3)", flexWrap: "wrap", alignItems: "center" }}
        >
          <span className="small strong">Based on your description, consider preferring:</span>
          <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
            {data.hints.suggested_nice_to_haves.map((key) => {
              const active = criteria.niceToHave.includes(key);
              return (
                <button
                  key={key}
                  type="button"
                  className={`btn btn--sm ${active ? "btn--primary" : "btn--secondary"}`}
                  onClick={() =>
                    setCriteria({
                      niceToHave: active
                        ? criteria.niceToHave.filter((k) => k !== key)
                        : [...criteria.niceToHave, key],
                    })
                  }
                  aria-pressed={active}
                >
                  {key.replace(/_/g, " ")}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      {chips.length > 0 ? (
        <div className="cluster" style={{ ["--cluster-gap" as string]: "8px", marginBottom: "var(--space-5)" }}>
          {chips.map((chip) => (
            <span className="chip" key={chip.key}>
              {chip.label}
              <button
                type="button"
                className="chip__remove"
                onClick={chip.clear}
                aria-label={`Remove filter: ${chip.label}`}
              >
                ×
              </button>
            </span>
          ))}
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={resetCriteria}
          >
            Clear all
          </button>
        </div>
      ) : null}

      {assistantOpen ? <AssistantPanel id="assistant-panel" /> : null}

      <div className="discover-layout">
        <aside className="discover-layout__aside" aria-label="Filters">
          <FilterPanel />
        </aside>

        <div>
          {/* Mobile filter trigger */}
          <div className="filters__mobile-bar">
            <button
              type="button"
              className="btn btn--secondary filters__mobile-trigger"
              onClick={() => setDrawerOpen(true)}
            >
              Filters
              {activeFilterCount > 0 ? (
                <span className="site-nav__count" aria-hidden="true">
                  {activeFilterCount}
                </span>
              ) : null}
            </button>
            <label className="sr-only" htmlFor="mobile-sort">
              Sort results
            </label>
            <select
              id="mobile-sort"
              className="select"
              value={criteria.sort}
              onChange={(e) => setCriteria({ sort: e.target.value as SortKey })}
              style={{ maxWidth: 190 }}
            >
              {Object.entries(SORT_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {error ? (
            <div className="state state--error" role="alert">
              <span className="state__icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
                  <path d="M12 7v6M12 16h.01" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
                </svg>
              </span>
              <p className="state__title">We could not load results</p>
              <p className="state__body">{error}</p>
              <button type="button" className="btn btn--primary btn--sm" onClick={retry}>
                Try again
              </button>
            </div>
          ) : loading ? (
            <>
              <div className="sr-only" role="status">
                Loading results
              </div>
              <div className="grid">
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <ProductCardSkeleton key={i} />
                ))}
              </div>
            </>
          ) : data && data.results.length > 0 ? (
            <>
              <div style={{ marginBottom: "var(--space-5)" }}>
                <DemoNotice notice={data.meta.important_notice} />
              </div>
              <div className="grid">
                {data.results.map((item) => (
                  <ProductCard key={`${item.product.product_id}-${item.offer.seller_id}`} item={item} />
                ))}
              </div>

              {data.rejected.length > 0 ? (
                <details className="card card--pad" style={{ marginTop: "var(--space-8)" }}>
                  <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                    {data.rejected.length} excluded{" "}
                    {data.rejected.length === 1 ? "option" : "options"} — why were they filtered out?
                  </summary>
                  <ul style={{ ["--flow" as string]: "var(--space-4)", marginTop: "var(--space-4)" }} className="stack">
                    {data.rejected.map((item) => (
                      <li key={`${item.product.product_id}-${item.offer.seller_id}`} className="small">
                        <span className="strong">{item.product.name}</span>{" "}
                        <span className="muted">
                          — {item.failed_constraints?.join(", ")}:{" "}
                          {item.failed_constraints?.includes("budget")
                            ? item.reasons.budget
                            : item.reasons.condition}
                        </span>
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </>
          ) : (
            <div className="state">
              <span className="state__icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.7" />
                  <path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                </svg>
              </span>
              <p className="state__title">Nothing matches every constraint</p>
              <p className="state__body">
                The assistant only removes a product when it fails a requirement you set. Try
                raising the budget or relaxing a required specification.
              </p>
              <div className="cluster" style={{ justifyContent: "center" }}>
                {criteria.budget !== null ? (
                  <button
                    type="button"
                    className="btn btn--secondary btn--sm"
                    onClick={() => setCriteria({ budget: null })}
                  >
                    Remove budget limit
                  </button>
                ) : null}
                {criteria.mustHave.length > 0 ? (
                  <button
                    type="button"
                    className="btn btn--secondary btn--sm"
                    onClick={() => setCriteria({ mustHave: [] })}
                  >
                    Remove required specs
                  </button>
                ) : null}
                <button type="button" className="btn btn--primary btn--sm" onClick={resetCriteria}>
                  Reset everything
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Filters"
        footer={
          <>
            <button
              type="button"
              className="btn btn--secondary"
              onClick={() => {
                resetCriteria();
                setDrawerOpen(false);
              }}
            >
              Reset
            </button>
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => setDrawerOpen(false)}
            >
              Show {data?.total_matched ?? 0} results
            </button>
          </>
        }
      >
        <FilterPanel />
      </Drawer>
    </div>
  );
}