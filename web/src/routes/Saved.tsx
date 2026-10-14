import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ProductDetailResponse } from "../api/types";
import { useSession } from "../state/SessionContext";
import { ProductVisual } from "../components/ProductVisual";
import { DemoNotice } from "../components/Layout";
import { CONDITION_LABEL, formatPrice } from "../utils/format";

export default function Saved() {
  const { saved, removeSaved, clearSaved, persistent, toggleCompare, isComparing } = useSession();
  const [items, setItems] = useState<ProductDetailResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (saved.length === 0) {
      setItems([]);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    // Each saved item is fetched from the real endpoint; nothing is cached client-side.
    Promise.all(
      saved.map((id) =>
        api
          .product(id, controller.signal)
          .catch(() => null),
      ),
    )
      .then((responses) => {
        if (controller.signal.aborted) return;
        setItems(responses.filter((r): r is ProductDetailResponse => r !== null));
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("Could not load your saved items.");
      })
      .finally(() => !controller.signal.aborted && setLoading(false));

    return () => controller.abort();
  }, [saved]);

  return (
    <div className="shell page">
      <div className="section-head">
        <div>
          <p className="eyebrow">Shortlist</p>
          <h1 style={{ fontSize: "var(--text-2xl)" }}>
            {saved.length === 0 ? "No saved items" : `Saved items (${saved.length})`}
          </h1>
          <p className="muted small" style={{ marginTop: "var(--space-2)", maxWidth: "58ch" }}>
            {persistent
              ? "Saved in this browser only. There is no account in this prototype, so nothing is synced between devices."
              : "This browser is blocking local storage, so saved items will disappear when you reload the page."}
          </p>
        </div>
        {saved.length > 0 ? (
          <button type="button" className="btn btn--secondary btn--sm" onClick={clearSaved}>
            Clear all
          </button>
        ) : null}
      </div>

      {!persistent ? (
        <div className="demo-notice" role="note" style={{ marginBottom: "var(--space-5)" }}>
          <span className="demo-notice__icon" aria-hidden="true">⚠</span>
          <span>
            <strong>Local storage is unavailable.</strong> Saved items and comparison selections will
            be lost when you close or reload this tab.
          </span>
        </div>
      ) : null}

      {saved.length === 0 ? (
        <div className="state">
          <span className="state__icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.5 9.7l5.9-.9L12 3.5Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <p className="state__title">Your shortlist is empty</p>
          <p className="state__body">
            Save products while you browse to keep them here for a side-by-side look later.
          </p>
          <Link to="/discover" className="btn btn--primary btn--sm">
            Find laptops
          </Link>
        </div>
      ) : error ? (
        <div className="state state--error" role="alert">
          <p className="state__title">Could not load saved items</p>
          <p className="state__body">{error}</p>
        </div>
      ) : loading ? (
        <div className="grid">
          {[0, 1, 2].map((i) => (
            <div className="skeleton" key={i} style={{ height: 220, borderRadius: 10 }} />
          ))}
        </div>
      ) : (
        <>
          <div style={{ marginBottom: "var(--space-6)" }}>
            <DemoNotice />
          </div>
          <div className="grid">
            {items.map((item) => {
              const offer = item.offers[0];
              return (
                <article className="product-card" key={item.product.product_id}>
                  <ProductVisual
                    productId={item.product.product_id}
                    name={item.product.name}
                    specs={item.product.specs}
                  />
                  <div className="product-card__body">
                    <div className="product-card__head">
                      <h3 className="product-card__name">
                        <Link to={`/product/${item.product.product_id}`}>{item.product.name}</Link>
                      </h3>
                      {offer ? (
                        <span className="product-card__price price">{formatPrice(offer.price_amount)}</span>
                      ) : null}
                    </div>
                    <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
                      {offer ? (
                        <span className="badge">
                          {CONDITION_LABEL[offer.condition] ?? offer.condition}
                        </span>
                      ) : null}
                      {item.unknown_fields.length > 0 ? (
                        <span className="badge badge--warn">
                          {item.unknown_fields.length} unknown{" "}
                          {item.unknown_fields.length === 1 ? "field" : "fields"}
                        </span>
                      ) : (
                        <span className="badge badge--ok">All specs on record</span>
                      )}
                    </div>
                  </div>
                  <div className="product-card__foot">
                    <button
                      type="button"
                      className="btn btn--ghost btn--sm"
                      onClick={() => removeSaved(item.product.product_id)}
                    >
                      Remove
                    </button>
                    <button
                      type="button"
                      className="btn btn--secondary btn--sm"
                      onClick={() => toggleCompare(item.product.product_id, item.product.name)}
                      aria-pressed={isComparing(item.product.product_id)}
                    >
                      {isComparing(item.product.product_id) ? "✓ Comparing" : "+ Compare"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}