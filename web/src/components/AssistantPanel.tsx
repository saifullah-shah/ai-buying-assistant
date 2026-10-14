import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { AssistantResponse } from "../api/types";
import { useSession } from "../state/SessionContext";

const STARTERS = [
  "Why does this shortlist suit me?",
  "Which of these is best value?",
  "What am I giving up by choosing the cheapest?",
  "Which one should I pick for programming?",
];

interface Turn {
  role: "user" | "assistant";
  text: string;
}

/**
 * Assistant panel.
 *
 * The reply always comes from the real `/api/assistant` endpoint, which either
 * calls the configured Gemini model through the existing M4 prompt builder or
 * falls back to a deterministic, clearly-labelled explanation. The UI shows the
 * backend's own `mode` and `notice` verbatim so a fabricated answer can never be
 * presented as a live AI response.
 */
export function AssistantPanel({ id }: { id?: string }) {
  const { criteria, lastResults } = useSession();
  const [turns, setTurns] = useState<Turn[]>([
    {
      role: "assistant",
      text: "Ask about the current shortlist. I explain each option against the specifications actually on record, and say so when something is unknown.",
    },
  ]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AssistantResponse | null>(null);

  async function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    setTurns((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setPending(true);
    setError(null);

    try {
      const result = await api.assistant({
        query: criteria.q?.trim() || trimmed,
        budget_amount: criteria.budget,
        budget_currency: "PKR",
        product_ids: lastResults.slice(0, 4).map((r) => r.productId),
        sort: criteria.sort,
      });
      setResponse(result);

      if (result.mode === "none") {
        setTurns((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "No options match your current constraints, so there is nothing to explain yet. Relax a filter or raise the budget first.",
          },
        ]);
        return;
      }

      const lines = result.explanations.map((exp) => {
        const parts = [`${exp.product_name}`, exp.fits_because, exp.what_it_sacrifices];
        if (exp.unknown_and_why.length) {
          parts.push(`Unknown: ${exp.unknown_and_why.join("; ")}`);
        }
        return parts.filter(Boolean).join("\n\n");
      });

      setTurns((prev) => [
        ...prev,
        { role: "assistant", text: lines.join("\n\n———\n\n") },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.detail
            ? `${err.message} — ${err.detail}`
            : err.message
          : "The assistant could not be reached.";
      setError(message);
      setTurns((prev) => [...prev, { role: "assistant", text: message }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="assistant" id={id} aria-label="Buying assistant">
      <div className="card card--pad">
        <div className="section-head" style={{ marginBottom: "var(--space-4)" }}>
          <div>
            <p className="eyebrow" style={{ marginBottom: "var(--space-1)" }}>
              Buying assistant
            </p>
            <p className="xsmall muted">
              Explanations are restricted to the {response?.shortlist_size ?? lastResults.length}{" "}
              options currently in your shortlist.
            </p>
          </div>
          {response ? (
            <span className={`badge badge--${response.mode === "live" ? "ok" : "warn"}`}>
              <span className="badge__dot" aria-hidden="true" />
              {response.mode === "live" ? "Live model" : response.mode === "demo" ? "Deterministic" : "Idle"}
            </span>
          ) : null}
        </div>

        {response ? (
          <div
            className={`demo-notice${response.mode === "live" ? "" : ""}`}
            role="note"
            style={
              response.mode === "live"
                ? { background: "var(--ok-soft)", borderColor: "var(--ok-border)", color: "#0a4d31" }
                : undefined
            }
          >
            {response.notice}
            {response.model ? (
              <span className="mono"> [{response.model}]</span>
            ) : null}
          </div>
        ) : null}

        <div className="assistant__log" style={{ marginTop: "var(--space-4)" }}>
          {turns.map((turn, index) => (
            <div key={index} className={`msg msg--${turn.role}`}>
              <span className="msg__label">{turn.role === "user" ? "You" : "Assistant"}</span>
              {turn.text.split("\n").map((line, i) => (
                <p key={i} style={{ whiteSpace: "pre-wrap", marginBottom: i === 0 ? 0 : "var(--space-2)" }}>
                  {line}
                </p>
              ))}
            </div>
          ))}
          {pending ? (
            <div className="msg msg--assistant" aria-live="polite">
              <span className="msg__label">Assistant</span>
              <span className="btn__spinner" aria-hidden="true" />{" "}
              <span className="muted">Working on it…</span>
            </div>
          ) : null}
        </div>

        {error ? (
          <p className="field__error" role="alert" style={{ marginTop: "var(--space-3)" }}>
            {error}
          </p>
        ) : null}

        <div className="assistant__composer" style={{ marginTop: "var(--space-5)" }}>
          <label className="field__label" htmlFor="assistant-input">
            Your question
          </label>
          <textarea
            id="assistant-input"
            className="textarea"
            value={input}
            placeholder="e.g. Which of these is best value for programming?"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                void send(input);
              }
            }}
          />
          <div className="assistant__actions">
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => void send(input)}
              disabled={pending || !input.trim()}
            >
              {pending ? "Thinking…" : "Ask"}
            </button>
            <span className="xsmall muted" style={{ alignSelf: "center" }}>
              Ctrl + Enter to send
            </span>
          </div>

          <div className="cluster" style={{ ["--cluster-gap" as string]: "6px", marginTop: "var(--space-2)" }}>
            {STARTERS.map((starter) => (
              <button
                key={starter}
                type="button"
                className="suggestion"
                onClick={() => void send(starter)}
                disabled={pending}
              >
                {starter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {response && response.explanations.length > 0 ? (
        <div className="card card--pad">
          <p className="eyebrow">Structured explanations</p>
          {response.explanations.map((exp) => (
            <article className="explain-block" key={exp.product_id}>
              <header className="explain-block__head">
                <span className="explain-block__title">
                  {exp.index}. {exp.product_name}
                </span>
                <Link
                  className="btn btn--ghost btn--sm"
                  to={`/product/${exp.product_id}`}
                >
                  View details
                </Link>
              </header>
              <div className="explain-section">
                <p className="explain-section__label">Fits because</p>
                <p className="small">{exp.fits_because}</p>
              </div>
              <div className="explain-section">
                <p className="explain-section__label">What it sacrifices</p>
                <p className="small">{exp.what_it_sacrifices}</p>
              </div>
              <div className="explain-section">
                <p className="explain-section__label">Unknown and why</p>
                <ul className="small" style={{ ["--flow" as string]: "4px" }}>
                  {exp.unknown_and_why.map((u, i) => (
                    <li key={i} className="muted">
                      {u}
                    </li>
                  ))}
                </ul>
              </div>
              {exp.constraint_summary ? (
                <div className="explain-section">
                  <p className="explain-section__label">Constraint compliance</p>
                  <pre className="mono xsmall muted" style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                    {exp.constraint_summary}
                  </pre>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}