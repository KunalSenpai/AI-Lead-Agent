import { CheckCircle2 } from "lucide-react";

interface ApprovalActionsProps {
  status: string | null | undefined;
  approving: boolean;
  rejecting: boolean;
  sending: boolean;
  onApprove: () => void;
  onReject: () => void;
  onSendClick: () => void;
}

// Renders exactly the actions the current email_status allows.
// The backend is the final authority — this only decides what buttons
// to *show*; every click still goes through a real backend call that
// can reject the transition.
export function ApprovalActions({
  status,
  approving,
  rejecting,
  sending,
  onApprove,
  onReject,
  onSendClick,
}: ApprovalActionsProps) {
  if (status === "pending_approval") {
    return (
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-danger" onClick={onReject} disabled={approving || rejecting}>
          {rejecting ? "Rejecting…" : "Reject"}
        </button>
        <button className="btn btn-success" onClick={onApprove} disabled={approving || rejecting}>
          {approving ? "Approving…" : "Approve"}
        </button>
      </div>
    );
  }

  if (status === "approved") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--success)", fontWeight: 600, fontSize: 13.5 }}>
          <CheckCircle2 size={16} /> Approved
        </span>
        <button className="btn btn-primary" onClick={onSendClick} disabled={sending}>
          {sending ? "Sending…" : "Send Email"}
        </button>
      </div>
    );
  }

  return null;
}
