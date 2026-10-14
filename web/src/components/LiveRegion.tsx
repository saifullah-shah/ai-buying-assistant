import { useSession } from "../state/SessionContext";

/** Announcements for screen readers (compare/save/add/remove results). */
export function LiveRegion() {
  const { compare, saved, activeFilterCount } = useSession();
  return (
    <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
      {compare.length} of 4 products selected for comparison. {saved.length} saved.{" "}
      {activeFilterCount} active{" "}
      {activeFilterCount === 1 ? "filter" : "filters"}.
    </div>
  );
}