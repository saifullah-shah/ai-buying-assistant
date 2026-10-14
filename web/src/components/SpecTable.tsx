import type { SpecView } from "../api/types";
import { formatNumber } from "../utils/format";

/** Accessible specification table. Unknown values are labelled, never blanked. */
export function SpecTable({
  specs,
  caption,
  onlyKnown = false,
}: {
  specs: SpecView[];
  caption?: string;
  onlyKnown?: boolean;
}) {
  const rows = onlyKnown ? specs.filter((s) => !s.is_unknown) : specs;
  if (rows.length === 0) {
    return <p className="muted small">No specifications are recorded for this product.</p>;
  }

  return (
    <table className="spec-table">
      {caption ? <caption>{caption}</caption> : null}
      <tbody>
        {rows.map((spec) => (
          <tr key={spec.key}>
            <th scope="row">{spec.label}</th>
            <td>
              {spec.is_unknown ? (
                <span className="spec-unknown">
                  Unknown
                  <span className="sr-only">
                    {" "}
                    — this specification is not disclosed in the source record
                  </span>
                </span>
              ) : (
                formatNumber(spec.value, spec.unit)
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}