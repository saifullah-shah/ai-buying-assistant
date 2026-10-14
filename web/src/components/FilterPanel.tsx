import { CONDITIONS, MUST_HAVE_OPTIONS, NICE_TO_HAVE_OPTIONS, SORT_LABELS, type SortKey } from "../api/types";
import { EMPTY_CRITERIA, useSession } from "../state/SessionContext";
import { PKR_BUDGET_SHORTCUTS } from "../utils/format";

function toggleIn(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

function NumField({
  id,
  label,
  value,
  onChange,
  suffix,
  hint,
}: {
  id: string;
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  suffix: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div style={{ position: "relative" }}>
        <input
          id={id}
          className="input"
          type="number"
          inputMode="numeric"
          min={0}
          step={suffix === "kg" ? 0.1 : 1}
          value={value ?? ""}
          placeholder="Any"
          onChange={(e) => {
            const raw = e.target.value;
            onChange(raw === "" ? null : Number(raw));
          }}
          style={{ paddingRight: 58 }}
        />
        <span
          className="xsmall muted"
          style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}
        >
          {suffix}
        </span>
      </div>
      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}

/** The filter controls, rendered identically in the desktop rail and the drawer. */
export function FilterPanel() {
  const { criteria, setCriteria, resetCriteria, activeFilterCount } = useSession();

  return (
    <div className="filters">
      <div className="filter-group">
        <h2 className="filter-group__title">Budget</h2>
        <div className="field">
          <label className="field__label" htmlFor="budget-input">
            Maximum price
          </label>
          <input
            id="budget-input"
            className="input"
            type="number"
            inputMode="numeric"
            min={1000}
            step={5000}
            value={criteria.budget ?? ""}
            placeholder="No limit"
            onChange={(e) =>
              setCriteria({ budget: e.target.value === "" ? null : Number(e.target.value) })
            }
          />
          <span className="field__hint">
            Products above this price are excluded, not just de-ranked.
          </span>
        </div>

        <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
          {PKR_BUDGET_SHORTCUTS.map((shortcut) => (
            <button
              key={shortcut.value}
              type="button"
              className={`btn btn--sm ${criteria.budget === shortcut.value ? "btn--primary" : "btn--secondary"}`}
              onClick={() =>
                setCriteria({
                  budget: criteria.budget === shortcut.value ? null : shortcut.value,
                })
              }
              aria-pressed={criteria.budget === shortcut.value}
            >
              {shortcut.label.replace("Under ", "<")}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <h2 className="filter-group__title">Condition</h2>
        <div role="group" aria-label="Condition">
          <div className="cluster" style={{ ["--cluster-gap" as string]: "6px" }}>
            {CONDITIONS.map((condition) => (
              <button
                key={condition}
                type="button"
                className={`btn btn--sm ${
                  criteria.condition === condition ? "btn--primary" : "btn--secondary"
                }`}
                onClick={() =>
                  setCriteria({ condition: criteria.condition === condition ? null : condition })
                }
                aria-pressed={criteria.condition === condition}
              >
                {condition[0].toUpperCase() + condition.slice(1)}
              </button>
            ))}
          </div>
          <p className="field__hint" style={{ marginTop: "var(--space-2)" }}>
            Leave unset to include every condition.
          </p>
        </div>
      </div>

      <div className="filter-group">
        <h2 className="filter-group__title">Required specs</h2>
        <p className="xsmall muted">
          A product must have a <em>known</em> value for every spec you require here. Missing or
          undisclosed values fail the check.
        </p>
        <div role="group" aria-label="Required specifications">
          {MUST_HAVE_OPTIONS.map((option) => (
            <label className="checkbox" key={option.key}>
              <input
                type="checkbox"
                checked={criteria.mustHave.includes(option.key)}
                onChange={() =>
                  setCriteria({ mustHave: toggleIn(criteria.mustHave, option.key) })
                }
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <h2 className="filter-group__title">Preferences</h2>
        <p className="xsmall muted">Preferred specs improve ranking. They never exclude a product.</p>
        <div role="group" aria-label="Preferred specifications">
          {NICE_TO_HAVE_OPTIONS.map((option) => (
            <label className="checkbox" key={option.key}>
              <input
                type="checkbox"
                checked={criteria.niceToHave.includes(option.key)}
                onChange={() =>
                  setCriteria({ niceToHave: toggleIn(criteria.niceToHave, option.key) })
                }
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <h2 className="filter-group__title">Specification limits</h2>
        <NumField
          id="min-ram"
          label="Minimum memory"
          suffix="GB"
          value={criteria.minRam}
          onChange={(v) => setCriteria({ minRam: v })}
        />
        <NumField
          id="min-storage"
          label="Minimum storage"
          suffix="GB"
          value={criteria.minStorage}
          onChange={(v) => setCriteria({ minStorage: v })}
        />
        <NumField
          id="min-screen"
          label="Minimum screen size"
          suffix="in"
          value={criteria.minScreen}
          onChange={(v) => setCriteria({ minScreen: v })}
        />
        <NumField
          id="max-weight"
          label="Maximum weight"
          suffix="kg"
          value={criteria.maxWeight}
          onChange={(v) => setCriteria({ maxWeight: v })}
        />
      </div>

      <div className="filter-group">
        <h2 className="filter-group__title">Sort by</h2>
        <label className="sr-only" htmlFor="sort-select">
          Sort results
        </label>
        <select
          id="sort-select"
          className="select"
          value={criteria.sort}
          onChange={(e) => setCriteria({ sort: e.target.value as SortKey })}
        >
          {Object.entries(SORT_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        className="btn btn--secondary btn--block"
        onClick={resetCriteria}
        disabled={activeFilterCount === 0 && criteria.sort === "relevance"}
      >
        Reset all filters
      </button>

      {activeFilterCount > 0 ? (
        <p className="xsmall muted" style={{ textAlign: "center" }}>
          {activeFilterCount} active{" "}
          {activeFilterCount === 1 ? "filter" : "filters"}
        </p>
      ) : null}
    </div>
  );
}

export { EMPTY_CRITERIA };