import { useState } from "react";
import { Pencil } from "lucide-react";
import type { Lead } from "../../types/lead";
import { approveLead, rejectLead, sendLeadEmail, updateEmail, ApiError } from "../../services/leadsApi";
import { useToast } from "../ui/Toast";
import { StatusBadge } from "../ui/StatusBadge";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { EmailEditor } from "./EmailEditor";
import { ApprovalActions } from "./ApprovalActions";
import { formatDateTime } from "../../utils/format";

interface EmailDraftCardProps {
  lead: Lead;
  onLeadUpdate: (lead: Lead) => void;
}

export function EmailDraftCard({ lead, onLeadUpdate }: EmailDraftCardProps) {
  const { showSuccess, showError } = useToast();
  const [editing, setEditing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [sending, setSending] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [confirmSendOpen, setConfirmSendOpen] = useState(false);

  async function handleApprove() {
    setApproving(true);
    try {
      const res = await approveLead(lead.id);
      onLeadUpdate(res.lead);
      showSuccess("Email approved successfully");
    } catch (e) {
      showError(e instanceof ApiError ? e.message : "Unable to approve email. Please try again.");
    } finally {
      setApproving(false);
    }
  }

  async function handleReject() {
    setRejecting(true);
    try {
      const res = await rejectLead(lead.id);
      onLeadUpdate(res.lead);
      showSuccess("Email rejected");
    } catch (e) {
      showError(e instanceof ApiError ? e.message : "Unable to reject email. Please try again.");
    } finally {
      setRejecting(false);
    }
  }

  async function handleSaveEmail(subject: string, body: string) {
    setSavingEmail(true);
    try {
      const res = await updateEmail(lead.id, { subject, body });
      onLeadUpdate(res.lead);
      setEditing(false);
      showSuccess("Email draft updated");
    } catch (e) {
      showError(e instanceof ApiError ? e.message : "Unable to save changes. Please try again.");
    } finally {
      setSavingEmail(false);
    }
  }

  async function handleSend() {
    setSending(true);
    try {
      const res = await sendLeadEmail(lead.id);
      onLeadUpdate(res.lead);
      showSuccess("Email sent successfully");
    } catch (e) {
      showError(e instanceof ApiError ? e.message : "Unable to send the email. Please try again.");
    } finally {
      setSending(false);
      setConfirmSendOpen(false);
    }
  }

  const status = lead.email_status;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div className="card-title" style={{ marginBottom: 0 }}>AI Generated Email</div>
        <StatusBadge status={status} />
      </div>

      {editing ? (
        <EmailEditor
          initialSubject={lead.email_subject || ""}
          initialBody={lead.email_body || ""}
          saving={savingEmail}
          onCancel={() => setEditing(false)}
          onSave={handleSaveEmail}
        />
      ) : (
        <div className="stack">
          <div>
            <div className="kv-label">Subject</div>
            <div className="kv-value" style={{ fontWeight: 600 }}>{lead.email_subject || "—"}</div>
          </div>
          <div>
            <div className="kv-label">Body</div>
            <div className="kv-value" style={{ whiteSpace: "pre-wrap" }}>{lead.email_body || "—"}</div>
          </div>

          {status === "sent" && lead.sent_at && (
            <p style={{ fontSize: 12.5, color: "var(--text-tertiary)" }}>
              Sent {formatDateTime(lead.sent_at)}
            </p>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10, marginTop: 4 }}>
            <div style={{ display: "flex", gap: 8 }}>
              {status === "pending_approval" && (
                <button className="btn btn-secondary" onClick={() => setEditing(true)}>
                  <Pencil size={14} /> Edit Email
                </button>
              )}
            </div>
            <ApprovalActions
              status={status}
              approving={approving}
              rejecting={rejecting}
              sending={sending}
              onApprove={handleApprove}
              onReject={handleReject}
              onSendClick={() => setConfirmSendOpen(true)}
            />
          </div>
        </div>
      )}

      <ConfirmDialog
        open={confirmSendOpen}
        title="Send this email?"
        description={`Send this email to ${lead.name} at ${lead.email}?`}
        confirmLabel="Send Email"
        loading={sending}
        onConfirm={handleSend}
        onCancel={() => setConfirmSendOpen(false)}
      />
    </div>
  );
}
