import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { CompareResponse } from "../api/types";
import { useSession, COMPARE_LIMIT } from "../state/SessionContext";
import { formatPrice } from "../utils/format";

/**
 * Comparison studio.
 *
 * Two rules drive the design:
 *  1. Missing data is shown as "Unknown", never as 0 or as a disadvantage.
 *  2. No single winner is declared — the "best" cell is only marked for
 *     attributes where a strictly better recorded value exists, and never for
 *     rows that are unknown.
 */
function bestIndex(row: CompareResponse["rows"][number]): number | null {
  // Only these rows have an unambiguous "more is better" direction.
  const higherIsBetter = new Set(["ram_gb", "storage_gb", "screen_size_in"]);
  if (!higherIsBetter.has(row.key)) return null;

  const values = row.cells.map((cell) =>
    cell.is_unknown || cell.value === null ? null : Number(cell.value),
  );
  const numbers = values.filter((v): v is number => v !== null && Number.isFinite(v));
  if (numbers.length < 2) return null;

  const max = Math.max(...numbers);
  if (numbers.filter((v) => v === max).length > 1) return null; // tie: no highlight
  const idx = values.indexOf(max);
  return idx === -1 ? null : idx;
}

export default function Compare() {
  const { compare, removeFromCompare, clearCompare } = useSession();
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (compare.length === 0) {
      setData(null);
      setError(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    api
      .compare(compare)
      .then(setData)
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof ApiError ? err.message : "Could not build the comparison.");
      })
      .finally(() => !controller.signal.aborted && setLoading(false));

    return () => controller.abort();
  }, [compare]);

  return (
    <div className="shell page">
      <div className="section-head">
        <div>
          <p className="eyebrow">Comparison studio</p>
          <h1 style={{ fontSize: "var(--text-2xl)" }}>
            {compare.length === 0
              ? "Nothing selected yet"
              : `Comparing ${compare.length} ${compare.length === 1 ? "product" : "products"}`}
          </h1>
          {compare.length > 0 ? (
            <p className="muted small" style={{ marginTop: "var(--space-2)" }}>
              Up to {COMPARE_LIMIT} products side by side. Unknown values are shown as unknown — they
              are never treated as zero.
            </p>
          ) : null}
        </div>
        {compare.length > 0 ? (
          <button type="button" className="btn btn--secondary btn--sm" onClick={clearCompare}>
            Clear comparison
          </button>
        ) : null}
      </div>

      {compare.length === 0 ? (
        <div className="state">
          <span className="state__icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="5" width="7" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
              <rect x="14" y="5" width="7" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
            </svg>
          </span>
          <p className="state__title">Add products to compare</p>
          <p className="state__body">
            Use the “Compare” button on any product card or detail page. Your selection is kept
            while you browse.
          </p>
          <Link to="/discover" className="btn btn--primary btn--sm">
            Find laptops
          </Link>
        </div>
      ) : error ? (
        <div className="state state--error" role="alert">
          <p className="state__title">Comparison unavailable</p>
          <p className="state__body">{error}</p>
        </div>
      ) : loading ? (
        <div className="skeleton" style={{ height: 380, borderRadius: 10 }} />
      ) : data ? (
        <>
          <div className="compare-scroll">
            <table className="compare-table">
              <caption className="sr-only">
                Side-by-side specification comparison of the selected demonstration laptops
              </caption>
              <thead>
                <tr>
                  <th className="compare-table__rowhead" scope="col">
                    Product
                  </th>
                  {data.products.map((entry) => (
                    <th scope="col" key={entry.product.product_id}>
                      <div className="compare-head">
                        <Link
                          to={`/product/${entry.product.product_id}`}
                          style={{ fontFamily: "var(--font-display)", fontSize: "var(--text-base)", color: "var(--ink)", textDecoration: "none" }}
                        >
                          {entry.product.name}
                        </Link>
                        <span className="price small">
                          {entry.offer ? formatPrice(entry.offer.price_amount) : "—"}
                        </span>
                        <span className="xsmall muted">
                          {entry.offer_count} seller{" "}
                          {entry.offer_count === 1 ? "record" : "records"}
                        </span>
                        <button
                          type="button"
                          className="btn btn--ghost btn--sm compare-head__remove"
                          onClick={() => removeFromCompare(entry.product.product_id)}
                          aria-label={`Remove ${entry.product.name} from comparison`}
                        >
                          Remove
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => {
                  const best = bestIndex(row);
                  return (
                    <tr key={row.key}>
                      <th className="compare-table__rowhead" scope="row">
                        {row.label}
                        {best !== null ? (
                          <span className="badge badge--ok" style={{ marginLeft: 8 }}>
                            Highest recorded
                          </span>
                        ) : null}
                      </th>
                      {row.cells.map((cell, i) => (
                        <td
                          key={i}
                          className={best === i ? "compare-table__cell--best" : undefined}
                        >
                          {cell.is_unknown ? (
                            <span className="compare-empty-cell">
                              Unknown
                              <span className="sr-only"> — not disclosed in the source record</span>
                            </span>
                          ) : (
                            cell.display
                          )}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="panel" style={{ marginTop: "var(--space-6)" }}>
            <p className="small">
              <strong>There is no overall winner.</strong> The highlighted column only marks the
              highest <em>recorded</em> value for memory, storage and screen size. A higher number
              is not automatically better for every buyer, and unknown fields are not counted
              against a product. Weight what matters to you before choosing.
            </p>
          </div>

          <div className="cluster" style={{ marginTop: "var(--space-6)" }}>
            <Link to="/discover" className="btn btn--secondary btn--sm">
              Add another product
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}