/**
 * Session state: active search criteria, comparison selection and saved items.
 *
 * Persistence rules (AGENTS.md + brief):
 * - Saved items and the comparison tray persist to `localStorage` so a reload
 *   does not lose the user's work.
 * - Every storage access is wrapped: private-mode browsers, disabled storage and
 *   corrupted JSON all degrade to in-memory state instead of crashing.
 * - A guest's saved list is **not** synced across devices and the UI never
 *   claims it is. There is no account system in this project.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { Condition, SortKey } from "../api/types";

const COMPARE_KEY = "aba.compare.v1";
const SAVED_KEY = "aba.saved.v1";
const QUERY_KEY = "aba.query.v1";
export const COMPARE_LIMIT = 4;

export interface SearchCriteria {
  q: string;
  budget: number | null;
  condition: Condition | null;
  mustHave: string[];
  niceToHave: string[];
  minRam: number | null;
  minStorage: number | null;
  maxWeight: number | null;
  minScreen: number | null;
  sort: SortKey;
}

export const EMPTY_CRITERIA: SearchCriteria = {
  q: "",
  budget: null,
  condition: null,
  mustHave: [],
  niceToHave: [],
  minRam: null,
  minStorage: null,
  maxWeight: null,
  minScreen: null,
  sort: "relevance",
};

/* ------------------------------------------------------------------ */
/* Safe storage                                                        */
/* ------------------------------------------------------------------ */

function readJSON<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return parsed ?? fallback;
  } catch {
    // Corrupted JSON, disabled storage, or a privacy mode that throws.
    return fallback;
  }
}

function writeJSON(key: string, value: unknown): boolean {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function removeKey(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

/** True when the browser let us write at least once this session. */
function storageAvailable(): boolean {
  const probe = "aba.probe";
  try {
    window.localStorage.setItem(probe, "1");
    window.localStorage.removeItem(probe);
    return true;
  } catch {
    return false;
  }
}

/* ------------------------------------------------------------------ */
/* Toast queue                                                         */
/* ------------------------------------------------------------------ */

export interface Toast {
  id: number;
  message: string;
  tone: "info" | "ok" | "danger";
}

interface ToastAction {
  type: "push" | "dismiss";
  toast?: Toast;
  id?: number;
}

function toastReducer(state: Toast[], action: ToastAction): Toast[] {
  if (action.type === "push" && action.toast) return [...state, action.toast];
  if (action.type === "dismiss") return state.filter((t) => t.id !== action.id);
  return state;
}

/* ------------------------------------------------------------------ */
/* Context                                                            */
/* ------------------------------------------------------------------ */

interface SessionValue {
  criteria: SearchCriteria;
  setCriteria: (next: Partial<SearchCriteria>) => void;
  resetCriteria: () => void;
  activeFilterCount: number;

  compare: string[];
  toggleCompare: (productId: string, name?: string) => void;
  removeFromCompare: (productId: string) => void;
  clearCompare: () => void;
  isComparing: (productId: string) => boolean;
  compareFull: boolean;

  saved: string[];
  toggleSaved: (productId: string, name?: string) => void;
  removeSaved: (productId: string) => void;
  isSaved: (productId: string) => boolean;
  clearSaved: () => void;

  persistent: boolean;
  toasts: Toast[];
  notify: (message: string, tone?: Toast["tone"]) => void;
  dismissToast: (id: number) => void;

  /** Search context used to return from a product page without losing state. */
  lastResults: { productId: string; name: string }[];
  setLastResults: (items: { productId: string; name: string }[]) => void;
}

const SessionContext = createContext<SessionValue | null>(null);

let toastSeq = 0;

export function SessionProvider({ children }: { children: ReactNode }) {
  const [persistent] = useState<boolean>(() => storageAvailable());
  const [compare, setCompare] = useState<string[]>(() =>
    readJSON<string[]>(COMPARE_KEY, []).filter((v) => typeof v === "string"),
  );
  const [saved, setSaved] = useState<string[]>(() =>
    readJSON<string[]>(SAVED_KEY, []).filter((v) => typeof v === "string"),
  );
  const [criteria, setCriteriaState] = useState<SearchCriteria>(() => {
    const stored = readJSON<Partial<SearchCriteria>>(QUERY_KEY, {});
    return { ...EMPTY_CRITERIA, ...stored };
  });
  const [lastResults, setLastResults] = useState<{ productId: string; name: string }[]>([]);
  const [toasts, dispatchToast] = useReducer(toastReducer, []);
  const timers = useRef<Map<number, number>>(new Map());

  /* ---- persistence ---- */
  useEffect(() => {
    if (persistent) writeJSON(COMPARE_KEY, compare);
  }, [compare, persistent]);

  useEffect(() => {
    if (persistent) writeJSON(SAVED_KEY, saved);
  }, [saved, persistent]);

  useEffect(() => {
    if (persistent) writeJSON(QUERY_KEY, criteria);
  }, [criteria, persistent]);

  /* ---- toasts ---- */
  const dismissToast = useCallback((id: number) => {
    dispatchToast({ type: "dismiss", id });
    const timer = timers.current.get(id);
    if (timer) {
      window.clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const notify = useCallback((message: string, tone: Toast["tone"] = "info") => {
    toastSeq += 1;
    const id = toastSeq;
    dispatchToast({ type: "push", toast: { id, message, tone } });
    const timer = window.setTimeout(() => {
      dispatchToast({ type: "dismiss", id });
      timers.current.delete(id);
    }, 4200);
    timers.current.set(id, timer);
  }, []);

  useEffect(() => {
    const map = timers.current;
    return () => {
      map.forEach((timer) => window.clearTimeout(timer));
      map.clear();
    };
  }, []);

  /* ---- criteria ---- */
  const setCriteria = useCallback((next: Partial<SearchCriteria>) => {
    setCriteriaState((prev) => ({ ...prev, ...next }));
  }, []);

  const resetCriteria = useCallback(() => {
    setCriteriaState(EMPTY_CRITERIA);
  }, []);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (criteria.budget !== null) count += 1;
    if (criteria.condition) count += 1;
    if (criteria.minRam !== null) count += 1;
    if (criteria.minStorage !== null) count += 1;
    if (criteria.maxWeight !== null) count += 1;
    if (criteria.minScreen !== null) count += 1;
    count += criteria.mustHave.length;
    count += criteria.niceToHave.length;
    return count;
  }, [criteria]);

  /* ---- comparison ---- */
  const compareFull = compare.length >= COMPARE_LIMIT;

  const toggleCompare = useCallback(
    (productId: string, name?: string) => {
      setCompare((prev) => {
        if (prev.includes(productId)) {
          notify(`Removed ${name ?? "product"} from comparison.`, "info");
          return prev.filter((id) => id !== productId);
        }
        if (prev.length >= COMPARE_LIMIT) {
          notify(
            `You can compare up to ${COMPARE_LIMIT} products. Remove one first.`,
            "danger",
          );
          return prev;
        }
        notify(`Added ${name ?? "product"} to comparison.`, "ok");
        return [...prev, productId];
      });
    },
    [notify],
  );

  const removeFromCompare = useCallback((productId: string) => {
    setCompare((prev) => prev.filter((id) => id !== productId));
  }, []);

  const clearCompare = useCallback(() => {
    setCompare([]);
    removeKey(COMPARE_KEY);
    notify("Comparison cleared.", "info");
  }, [notify]);

  const isComparing = useCallback((productId: string) => compare.includes(productId), [compare]);

  /* ---- saved ---- */
  const toggleSaved = useCallback(
    (productId: string, name?: string) => {
      setSaved((prev) => {
        if (prev.includes(productId)) {
          notify(`Removed ${name ?? "product"} from saved items.`, "info");
          return prev.filter((id) => id !== productId);
        }
        notify(`Saved ${name ?? "product"} to your shortlist.`, "ok");
        return [...prev, productId];
      });
    },
    [notify],
  );

  const removeSaved = useCallback((productId: string) => {
    setSaved((prev) => prev.filter((id) => id !== productId));
  }, []);

  const clearSaved = useCallback(() => {
    setSaved([]);
    removeKey(SAVED_KEY);
    notify("Saved items cleared.", "info");
  }, [notify]);

  const isSaved = useCallback((productId: string) => saved.includes(productId), [saved]);

  const value = useMemo<SessionValue>(
    () => ({
      criteria,
      setCriteria,
      resetCriteria,
      activeFilterCount,
      compare,
      toggleCompare,
      removeFromCompare,
      clearCompare,
      isComparing,
      compareFull,
      saved,
      toggleSaved,
      removeSaved,
      isSaved,
      clearSaved,
      persistent,
      toasts,
      notify,
      dismissToast,
      lastResults,
      setLastResults,
    }),
    [
      criteria, setCriteria, resetCriteria, activeFilterCount,
      compare, toggleCompare, removeFromCompare, clearCompare, isComparing, compareFull,
      saved, toggleSaved, removeSaved, isSaved, clearSaved,
      persistent, toasts, notify, dismissToast, lastResults,
    ],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside <SessionProvider>");
  return ctx;
}