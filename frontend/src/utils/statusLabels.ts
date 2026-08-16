import type { EmailStatus } from "../types/lead";

// Display-only mapping of the backend's real status/category values to
// human-friendly labels. The values themselves (pending_approval, Hot,
// etc.) always come from the backend — nothing is computed here.

export const STATUS_LABELS: Record<string, string> = {
  pending_approval: "Pending Approval",
  approved: "Approved",
  rejected: "Rejected",
  sent: "Sent",
};

export function statusLabel(status: string | null | undefined): string {
  if (!status) return "Unknown";
  return STATUS_LABELS[status] ?? status;
}

export function isKnownStatus(status: string | null | undefined): status is EmailStatus {
  return !!status && status in STATUS_LABELS;
}

export function categoryEmoji(category: string | null | undefined): string {
  switch ((category || "").toLowerCase()) {
    case "hot":
      return "🔥";
    case "warm":
      return "🌤";
    case "cold":
      return "❄️";
    default:
      return "";
  }
}
