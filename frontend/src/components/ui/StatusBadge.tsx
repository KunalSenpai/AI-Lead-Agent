import { Clock, CheckCircle2, XCircle, Send, type LucideIcon } from "lucide-react";
import type { CSSProperties } from "react";
import { statusLabel } from "../../utils/statusLabels";

interface StatusBadgeProps {
  status: string | null | undefined;
}

const STYLES: Record<
  string,
  { bg: string; fg: string; icon: LucideIcon }
> = {
  pending_approval: { bg: "var(--warm-tint)", fg: "#9A6300", icon: Clock },
  approved: { bg: "var(--success-tint)", fg: "#0A7A4B", icon: CheckCircle2 },
  rejected: { bg: "var(--danger-tint)", fg: "#B4232A", icon: XCircle },
  sent: { bg: "var(--success-tint)", fg: "#0A7A4B", icon: Send },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = (status && STYLES[status]) || {
    bg: "var(--surface-sunken)",
    fg: "var(--text-secondary)",
    icon: Clock,
  };
  const Icon = style.icon;

  const wrapperStyle: CSSProperties = {
    background: style.bg,
    color: style.fg,
  };

  return (
    <span className="badge" style={wrapperStyle}>
      <Icon size={13} />
      {statusLabel(status)}
    </span>
  );
}
