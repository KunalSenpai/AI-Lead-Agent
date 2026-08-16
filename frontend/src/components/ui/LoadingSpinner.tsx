interface LoadingSpinnerProps {
  label?: string;
  size?: number;
  inline?: boolean;
}

export function LoadingSpinner({ label, size = 20, inline = false }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        justifyContent: inline ? "flex-start" : "center",
        padding: inline ? 0 : "48px 0",
        color: "var(--text-secondary)",
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          border: "2.5px solid var(--border-strong)",
          borderTopColor: "var(--brand)",
          animation: "spin 0.7s linear infinite",
          flexShrink: 0,
        }}
      />
      {label && <span>{label}</span>}
      <span className="sr-only">Loading</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
