import { AlertTriangle, RotateCcw } from "lucide-react";

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        background: "var(--danger-tint)",
        color: "#8E1E24",
        border: "1px solid #F3C6C8",
        borderRadius: "var(--radius-md)",
        padding: "12px 14px",
        fontSize: 13.5,
      }}
    >
      <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
      <div style={{ flex: 1 }}>
        <p>{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              marginTop: 8,
              background: "none",
              border: "none",
              padding: 0,
              color: "#8E1E24",
              fontWeight: 600,
              textDecoration: "underline",
            }}
          >
            <RotateCcw size={13} /> Try again
          </button>
        )}
      </div>
    </div>
  );
}
