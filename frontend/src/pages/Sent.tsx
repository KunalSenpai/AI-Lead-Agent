import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Send } from "lucide-react";
import { useLeads } from "../hooks/useLeads";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { StatusBadge } from "../components/ui/StatusBadge";
import { formatDateTime } from "../utils/format";

export function Sent() {
  const { leads, loading, error, reload } = useLeads("sent");
  const navigate = useNavigate();

  const sent = useMemo(
    () =>
      leads
        .filter((l) => l.email_status === "sent")
        .sort((a, b) => (b.sent_at || "").localeCompare(a.sent_at || "")),
    [leads]
  );

  if (loading) return <LoadingSpinner label="Loading sent emails…" />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div>
      <div className="page-header">
        <h2>Sent</h2>
      </div>

      {sent.length === 0 ? (
        <EmptyState icon={Send} title="No emails have been sent yet" description="Approved emails you send will show up here." />
      ) : (
        <div className="table-wrap responsive">
          <table className="lead-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Company</th>
                <th>Subject</th>
                <th>Sent At</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sent.map((lead) => (
                <tr
                  key={lead.id}
                  tabIndex={0}
                  onClick={() => navigate(`/leads/${lead.id}`)}
                  onKeyDown={(e) => e.key === "Enter" && navigate(`/leads/${lead.id}`)}
                >
                  <td data-label="Lead">
                    <div className="lead-name">{lead.name}</div>
                    <div className="lead-sub">{lead.email}</div>
                  </td>
                  <td data-label="Company">{lead.company}</td>
                  <td data-label="Subject">{lead.email_subject || "—"}</td>
                  <td data-label="Sent At" className="lead-sub">{formatDateTime(lead.sent_at)}</td>
                  <td data-label="Status">
                    <StatusBadge status={lead.email_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
