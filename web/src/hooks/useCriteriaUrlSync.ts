/**
 * Keeps the active search criteria in sync with the URL query string.
 *
 * Why this exists:
 * - a search becomes shareable and bookmarkable,
 * - the browser back/forward buttons behave correctly,
 * - refreshing the page does not silently drop the user's filters.
 *
 * Precedence rule (important): when the URL carries **any** recognised search
 * parameter, the URL *defines* the whole search and persisted session criteria
 * are replaced rather than merged. Otherwise a shared link would silently
 * inherit the recipient's earlier filters and show different results from the
 * sender's. When the URL carries nothing, the persisted session criteria are
 * kept, so a plain refresh does not lose the user's work.
 *
 * The localStorage-backed session store remains the source of truth for
 * compare/saved selections; this hook only mirrors the *search* into the URL.
 */
import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import type { Condition, SortKey } from "../api/types";
import { EMPTY_CRITERIA, useSession, type SearchCriteria } from "../state/SessionContext";

const NUMERIC: Array<[keyof SearchCriteria, string]> = [
  ["budget", "budget"],
  ["minRam", "min_ram"],
  ["minStorage", "min_storage"],
  ["maxWeight", "max_weight"],
  ["minScreen", "min_screen"],
];

const VALID_CONDITIONS = ["new", "refurbished", "used", "open-box"];

/** Parse a query string into a full criteria object plus "did it express a search?". */
function parseCriteria(params: URLSearchParams): { criteria: SearchCriteria; hadAny: boolean } {
  let hadAny = false;
  const next: SearchCriteria = { ...EMPTY_CRITERIA };

  const q = params.get("q");
  if (q !== null) {
    next.q = q;
    hadAny = true;
  }

  for (const [field, param] of NUMERIC) {
    const raw = params.get(param);
    if (raw === null) continue;
    hadAny = true;
    const value = Number(raw);
    if (Number.isFinite(value) && value > 0) {
      (next as unknown as Record<string, unknown>)[field] = value;
    }
  }

  const condition = params.get("condition");
  if (condition !== null) {
    hadAny = true;
    if (VALID_CONDITIONS.includes(condition)) next.condition = condition as Condition;
  }

  const sort = params.get("sort");
  if (sort !== null) {
    hadAny = true;
    next.sort = sort as SortKey;
  }

  const must = params.getAll("must_have");
  if (must.length) {
    hadAny = true;
    next.mustHave = must;
  }

  const nice = params.getAll("nice_to_have");
  if (nice.length) {
    hadAny = true;
    next.niceToHave = nice;
  }

  return { criteria: next, hadAny };
}

/** Serialise criteria to a query string (no leading "?"). */
export function criteriaToSearchParams(criteria: SearchCriteria): URLSearchParams {
  const params = new URLSearchParams();
  if (criteria.q.trim()) params.set("q", criteria.q.trim());
  for (const [field, param] of NUMERIC) {
    const value = criteria[field];
    if (typeof value === "number" && Number.isFinite(value) && value > 0) {
      params.set(param, String(value));
    }
  }
  if (criteria.condition) params.set("condition", criteria.condition);
  if (criteria.sort && criteria.sort !== "relevance") params.set("sort", criteria.sort);
  for (const key of criteria.mustHave) params.append("must_have", key);
  for (const key of criteria.niceToHave) params.append("nice_to_have", key);
  return params;
}

export function useCriteriaUrlSync() {
  const { criteria, setCriteria } = useSession();
  const [searchParams, setSearchParams] = useSearchParams();
  const hydrated = useRef(false);

  // --- hydrate once from the URL -------------------------------------------
  useEffect(() => {
    if (hydrated.current) return;
    const { criteria: parsed, hadAny } = parseCriteria(searchParams);
    if (hadAny) setCriteria(parsed); // replace, not merge
    hydrated.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- mirror criteria back into the URL ------------------------------------
  useEffect(() => {
    if (!hydrated.current) return;
    // replaceState semantics: typing in the search box must not fill history.
    setSearchParams(criteriaToSearchParams(criteria), { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [criteria]);
}