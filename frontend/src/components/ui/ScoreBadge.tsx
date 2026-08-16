import { CSSProperties } from "react";

interface ScoreBadgeProps {
  category: string | null | undefined;
  score?: number | null;
  size?: "sm" | "md";
}

const CATEGORY_STYLES: Record<string, { bg: string; fg: string; emoji: string }> = {
  hot: { bg: "var(--hot-tint)", fg: "#B4232A", emoji: "🔥" },
  warm: { bg: "var(--warm-tint)", fg: "#9A6300", emoji: "🌤" },
  cold: { bg: "var(--cold-tint)", fg: "#2B4E9E", emoji: "❄️" },
};

export function ScoreBadge({ category, score, size = "sm" }: ScoreBadgeProps) {
  const key = (category || "").toLowerCase();
  const style = CATEGORY_STYLES[key] || {
    bg: "var(--surface-sunken)",
    fg: "var(--text-secondary)",
    emoji: "",
  };

  const wrapperStyle: CSSProperties = {
    background: style.bg,
    color: style.fg,
    fontSize: size === "md" ? 14 : 12,
    padding: size === "md" ? "6px 12px" : "3px 9px",
  };

  return (
    <span className="badge" style={wrapperStyle}>
      <span aria-hidden="true">{style.emoji}</span>
      {category || "Unscored"}
      {typeof score === "number" && (
        <span className="tabular" style={{ opacity: 0.75 }}>
          {" "}
          · {score}
        </span>
      )}
    </span>
  );
}
