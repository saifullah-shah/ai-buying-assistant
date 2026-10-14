import { Link } from "react-router-dom";
import type { ResultView } from "../api/types";
import { ProductVisual } from "./ProductVisual";
import { CONDITION_LABEL, FRESHNESS_LABEL, formatPrice } from "../utils/format";
import { useSession } from "../state/SessionContext";

const HIGHLIGHT_KEYS = ["ram_gb", "storage_gb", "screen_size_in"];

export function ProductCard({ item }: { item: ResultView }) {
  const { product, offer } = item;
  const { isComparing, toggleCompare, isSaved, toggleSaved, compareFull } = useSession();

  const comparing = isComparing(product.product_id);
  const saved = isSaved(product.product_id);
  const highlights = HIGHLIGHT_KEYS.map((key) =>
    product.specs.find((s) => s.key === key),
  ).filter((s): s is NonNullable<typeof s> => Boolean(s));

  const nth =
    item.matches.nice_to_haves_total > 0
      ? `${item.matches.nice_to_haves_score}/${item.matches.nice_to_haves_total}`
      : null;

  return (
    <article className="product-card" data-selected={comparing}>
      <ProductVisual
        productId={product.product_id}
        name={product.name}
        specs={product.specs}
      />

      <div className="product-card__body">
        <div className="product-card__head">
          <h3 className="product-card__name">
            <Link to={`/product/${product.product_id}`}>{product.name}</Link>
          </h3>
          <span className="product-card__price price">{formatPrice(offer.price_amount)}</span>
        </div>

        <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
          <span className="badge">{CONDITION_LABEL[offer.condition] ?? offer.condition}</span>
          <span className={`badge badge--${offer.freshness === "fresh" ? "ok" : "warn"}`}>
            <span className="badge__dot" aria-hidden="true" />
            {FRESHNESS_LABEL[offer.freshness]}
          </span>
          {nth ? <span className="badge badge--accent">Prefers {nth}</span> : null}
        </div>

        <div className="product-card__specs">
          {highlights.map((spec) => (
            <span
              key={spec.key}
              className={`spec-pill${spec.is_unknown ? " spec-pill--unknown" : ""}`}
            >
              <span className="spec-pill__k">{spec.label}</span>
              <span className="spec-pill__v">
                {spec.is_unknown ? "Unknown" : `${spec.value}${spec.unit ? ` ${spec.unit}` : ""}`}
              </span>
            </span>
          ))}
        </div>
      </div>

      <div className="product-card__foot">
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={() => toggleSaved(product.product_id, product.name)}
          aria-pressed={saved}
        >
          {saved ? "★ Saved" : "☆ Save"}
        </button>
        <button
          type="button"
          className="btn btn--secondary btn--sm"
          onClick={() => toggleCompare(product.product_id, product.name)}
          aria-pressed={comparing}
          disabled={!comparing && compareFull}
          title={
            !comparing && compareFull ? "Comparison is full (4 products)" : undefined
          }
        >
          {comparing ? "✓ In comparison" : "+ Compare"}
        </button>
      </div>
    </article>
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="skeleton skeleton-card__visual" />
      <div className="skeleton skeleton-card__line" style={{ width: "70%" }} />
      <div className="skeleton skeleton-card__line" style={{ width: "45%" }} />
      <div className="skeleton skeleton-card__line" style={{ width: "85%", height: 26 }} />
    </div>
  );
}