import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { DiscoverResponse, HealthResponse } from "../api/types";
import { DemoNotice } from "../components/Layout";
import { ProductCard, ProductCardSkeleton } from "../components/ProductCard";
import { useSession } from "../state/SessionContext";
import { formatPrice } from "../utils/format";

const EXAMPLES = [
  "Find me a laptop for university under Rs. 150,000.",
  "I need a laptop for programming and machine learning.",
  "Compare lightweight laptops for office work.",
  "Which laptop offers the best value for gaming?",
];

const STEPS = [
  {
    n: "01",
    title: "You describe the need",
    body: "Plain language and a budget in rupees. No specification jargon required.",
  },
  {
    n: "02",
    title: "Constraints run in code",
    body: "Budget, condition and must-have requirements are checked by deterministic code before anything is ranked.",
  },
  {
    n: "03",
    title: "You see the trade-offs",
    body: "Each option explains what it fits, what it gives up, and which facts are genuinely unknown.",
  },
];

export default function Home() {
  const navigate = useNavigate();
  const { setCriteria } = useSession();
  const [draft, setDraft] = useState("");
  const [budget, setBudget] = useState<string>("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [featured, setFeatured] = useState<DiscoverResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    Promise.all([api.health(), api.discover({ sort: "price_asc" })])
      .then(([h, d]) => {
        if (!alive) return;
        setHealth(h);
        setFeatured(d);
      })
      .catch(() => {
        /* the Discover page surfaces connection errors in context */
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  function startSearch(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setCriteria({
      q: draft.trim(),
      budget: budget.trim() === "" ? null : Number(budget),
      condition: null,
      mustHave: [],
      niceToHave: [],
      minRam: null,
      minStorage: null,
      maxWeight: null,
      minScreen: null,
      sort: "relevance",
    });
    navigate("/discover");
  }

  function useExample(example: string) {
    setDraft(example);
    const match = example.match(/Rs\.?\s*([\d,]+)/i);
    setBudget(match ? match[1].replace(/[, ]/g, "") : "");
  }

  const llmLive = health?.llm?.api_key_present === true;

  return (
    <>
      {/* ---------------- Hero ---------------- */}
      <section className="shell" style={{ paddingTop: "var(--space-16)", paddingBottom: "var(--space-12)" }}>
        <div className="home-hero">
          <div style={{ ["--flow" as string]: "var(--space-6)" }} className="stack">
            <p className="eyebrow">Pakistan · Laptops · Demonstration data</p>
            <h1
              style={{
                fontSize: "var(--text-4xl)",
                maxWidth: "15ch",
                marginBottom: "var(--space-2)",
              }}
            >
              Stop scrolling. Start deciding.
            </h1>
            <p className="lede" style={{ fontSize: "var(--text-lg)" }}>
              Tell the assistant what you need and what you can spend. It filters against your real
              budget first, then shows exactly what each remaining laptop gives up — and which
              facts it simply does not know.
            </p>

            <form
              onSubmit={startSearch}
              className="card card--pad"
              style={{ marginTop: "var(--space-4)", maxWidth: 620 }}
            >
              <div className="field">
                <label className="field__label" htmlFor="hero-query">
                  What are you buying, and for what?
                </label>
                <input
                  id="hero-query"
                  className="input"
                  type="text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="A laptop for university under Rs. 150,000"
                  autoComplete="off"
                />
              </div>

              <div className="field" style={{ marginTop: "var(--space-4)" }}>
                <label className="field__label" htmlFor="hero-budget">
                  Maximum budget (PKR)
                </label>
                <input
                  id="hero-budget"
                  className="input"
                  type="number"
                  inputMode="numeric"
                  min={1000}
                  step={5000}
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="150000"
                />
                <span className="field__hint">
                  Anything above this price is excluded entirely, not merely ranked lower.
                </span>
              </div>

              <button
                type="submit"
                className="btn btn--primary btn--lg btn--block"
                style={{ marginTop: "var(--space-5)" }}
                disabled={busy}
              >
                Find my options
              </button>
            </form>

            <div>
              <p className="xsmall muted" style={{ marginBottom: "var(--space-2)" }}>
                Try one of these:
              </p>
              <div className="cluster" style={{ ["--cluster-gap" as string]: "8px" }}>
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    className="suggestion"
                    onClick={() => useExample(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Live status card */}
          <aside className="card card--pad home-hero__aside" aria-label="Assistant status">
            <p className="eyebrow">Assistant status</p>
            <dl style={{ ["--flow" as string]: "var(--space-3)" }} className="stack">
              <div>
                <dt className="xsmall muted">Explanations</dt>
                <dd style={{ margin: 0 }}>
                  <span className={`badge badge--${llmLive ? "ok" : "warn"}`}>
                    <span className="badge__dot" aria-hidden="true" />
                    {llmLive ? "Live model available" : "Deterministic mode"}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="xsmall muted">Hard constraints</dt>
                <dd style={{ margin: 0 }}>
                  <span className="badge badge--ok">
                    <span className="badge__dot" aria-hidden="true" />
                    Enforced by code
                  </span>
                </dd>
              </div>
              <div>
                <dt className="xsmall muted">Catalogue</dt>
                <dd className="small" style={{ margin: 0 }}>
                  {loading ? "Loading…" : `${featured?.total_matched ?? 0} synthetic laptops`}
                </dd>
              </div>
            </dl>

            <hr />

            <p className="xsmall muted">
              {llmLive
                ? "Explanations are generated by the configured Gemini model and are checked for the required sections before display."
                : "No language model is configured, so explanations are generated deterministically from the catalogue and clearly labelled as such."}
            </p>
          </aside>
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="shell" aria-labelledby="how-heading" style={{ paddingBottom: "var(--space-16)" }}>
        <div className="section-head">
          <div>
            <p className="eyebrow">Method</p>
            <h2 id="how-heading">How recommendations are made</h2>
          </div>
        </div>
        <ol className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))" }}>
          {STEPS.map((step) => (
            <li className="card card--pad" key={step.n}>
              <p className="mono xsmall muted">{step.n}</p>
              <h3 style={{ fontSize: "var(--text-md)", margin: "var(--space-2) 0 var(--space-2)" }}>
                {step.title}
              </h3>
              <p className="small muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------- Featured ---------------- */}
      <section className="shell" aria-labelledby="featured-heading" style={{ paddingBottom: "var(--space-12)" }}>
        <div className="section-head">
          <div>
            <p className="eyebrow">From the catalogue</p>
            <h2 id="featured-heading">Lowest-priced options on record</h2>
          </div>
          <Link to="/discover" className="btn btn--secondary btn--sm">
            See all results
          </Link>
        </div>

        <div style={{ marginBottom: "var(--space-6)" }}>
          <DemoNotice />
        </div>

        {loading ? (
          <div className="grid">
            {[0, 1, 2, 3].map((i) => (
              <ProductCardSkeleton key={i} />
            ))}
          </div>
        ) : featured && featured.results.length > 0 ? (
          <div className="grid">
            {featured.results.slice(0, 4).map((item) => (
              <ProductCard key={item.product.product_id} item={item} />
            ))}
          </div>
        ) : (
          <p className="muted small">No demonstration records are available right now.</p>
        )}
      </section>

      {/* ---------------- Use cases ---------------- */}
      <section className="shell" aria-labelledby="usecase-heading" style={{ paddingBottom: "var(--space-8)" }}>
        <div className="section-head">
          <div>
            <p className="eyebrow">Shop by need</p>
            <h2 id="usecase-heading">Common starting points</h2>
          </div>
        </div>
        <div className="cluster" style={{ ["--cluster-gap" as string]: "var(--space-3)" }}>
          {[
            { label: "University study", budget: 150000 },
            { label: "Programming", budget: 200000 },
            { label: "Light office work", budget: 250000 },
            { label: "Machine learning", budget: 300000 },
          ].map((useCase) => (
            <button
              key={useCase.label}
              type="button"
              className="btn btn--secondary"
              onClick={() => {
                setCriteria({
                  q: `${useCase.label} laptop`,
                  budget: useCase.budget,
                  condition: null,
                  mustHave: [],
                  niceToHave: [],
                  minRam: null,
                  minStorage: null,
                  maxWeight: null,
                  minScreen: null,
                  sort: "relevance",
                });
                navigate("/discover");
              }}
            >
              {useCase.label}
              <span className="small muted">
                {formatPrice(useCase.budget)}
              </span>
            </button>
          ))}
        </div>
      </section>
    </>
  );
}