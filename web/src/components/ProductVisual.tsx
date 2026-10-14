/**
 * Generated product artwork.
 *
 * The curated dataset deliberately contains **no product images**, and this
 * project has no verified right to display retailer or manufacturer imagery.
 * Rather than hot-linking images that may break or infringe, we render a
 * deterministic abstract mark derived from the product id and its own recorded
 * specifications. It is honest (it is obviously not a photograph), stable across
 * reloads, and costs no network request.
 */
import { hashIndex, splitName } from "../utils/format";
import type { SpecView } from "../api/types";

interface Props {
  productId: string;
  name: string;
  specs: SpecView[];
  variant?: "card" | "hero";
}

const PALETTES = [
  { bg: "#eef1f7", line: "#2b4fd6", accent: "#8fa3ea" },
  { bg: "#f4f0e8", line: "#8a6a2f", accent: "#d3bb8b" },
  { bg: "#eef5f1", line: "#0f7b4f", accent: "#93c9ae" },
  { bg: "#f6eff1", line: "#9c3b52", accent: "#dda7b3" },
  { bg: "#eff1f5", line: "#42506b", accent: "#a3aec4" },
];

function specNumber(specs: SpecView[], key: string): number | null {
  const found = specs.find((s) => s.key === key && !s.is_unknown);
  const value = found?.value;
  return typeof value === "number" ? value : null;
}

export function ProductVisual({ productId, name, specs, variant = "card" }: Props) {
  const palette = PALETTES[hashIndex(productId, PALETTES.length)];
  const { head, tail } = splitName(name);
  const seed = hashIndex(productId, 1000) / 1000;

  // Geometry is derived from the record so different products look different,
  // but the same product always looks the same.
  const barCount = 3 + (specNumber(specs, "ram_gb") ?? 4);
  const bars = Array.from({ length: Math.min(barCount, 7) }, (_, i) => {
    const h = 22 + ((seed * 100 + i * 37) % 56);
    return h;
  });

  const width = variant === "hero" ? 520 : 300;
  const height = variant === "hero" ? 325 : 225;

  return (
    <div
      className={`visual visual--${variant}`}
      role="img"
      aria-label={`Abstract placeholder graphic for ${name}. No product photograph is available for this demonstration record.`}
    >
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <rect width={width} height={height} fill={palette.bg} />

        {/* deterministic contour lines */}
        {Array.from({ length: 5 }, (_, i) => (
          <path
            key={`c${i}`}
            d={`M -20 ${70 + i * 34} Q ${width * 0.3} ${40 + i * 34 + seed * 20} ${width * 0.55} ${
              80 + i * 30
            } T ${width + 20} ${60 + i * 32}`}
            fill="none"
            stroke={palette.accent}
            strokeOpacity={0.5 - i * 0.07}
            strokeWidth={variant === "hero" ? 1.6 : 1.2}
          />
        ))}

        {/* a schematic silhouette, not a photo */}
        <g opacity="0.9">
          <rect
            x={width * 0.18}
            y={height * 0.3}
            width={width * 0.64}
            height={height * 0.38}
            rx={6}
            fill="none"
            stroke={palette.line}
            strokeWidth={variant === "hero" ? 2.4 : 1.8}
          />
          <rect
            x={width * 0.24}
            y={height * 0.36}
            width={width * 0.52}
            height={height * 0.24}
            rx={3}
            fill={palette.accent}
            fillOpacity="0.35"
          />
          <path
            d={`M ${width * 0.12} ${height * 0.74} h ${width * 0.76}`}
            stroke={palette.line}
            strokeWidth={variant === "hero" ? 2.4 : 1.8}
            strokeLinecap="round"
          />
        </g>

        {/* spec-derived bar marks */}
        <g transform={`translate(${width * 0.24}, ${height * 0.79})`}>
          {bars.map((h, i) => (
            <rect
              key={`b${i}`}
              x={i * (variant === "hero" ? 13 : 9)}
              y={-(h / 3)}
              width={variant === "hero" ? 6 : 4}
              height={h / 3}
              rx={2}
              fill={palette.line}
              fillOpacity={0.55}
            />
          ))}
        </g>
      </svg>

      <span className="visual__tag" aria-hidden="true">
        Illustration · no photo
      </span>
      <span className="sr-only">
        {head}
        {tail ? ` ${tail}` : ""}
      </span>
    </div>
  );
}