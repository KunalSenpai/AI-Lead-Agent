import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, Flame, Clock, Send, ArrowRight } from "lucide-react";
import { useLeads } from "../hooks/useLeads";
import { LeadTable } from "../components/leads/LeadTable";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { syncGmail } from "../services/leadsApi";

export function Dashboard() {
  const { leads, loading, error, reload } = useLeads();
  const navigate = useNavigate();

  const [syncingGmail, setSyncingGmail] = useState(false);
  const [gmailSyncMessage, setGmailSyncMessage] = useState<string | null>(null);
  const [gmailSyncError, setGmailSyncError] = useState<string | null>(null);

  const handleGmailSync = async () => {
  setSyncingGmail(true);
  setGmailSyncMessage(null);
  setGmailSyncError(null);

  try {
    const result = await syncGmail();

    setGmailSyncMessage(
      result.leads_created === 0
        ? "Gmail is up to date. No new leads found."
        : `Gmail sync complete — ${result.leads_created} new lead${
            result.leads_created === 1 ? "" : "s"
          } found.`
    );

    await reload();
  } catch (e) {
    setGmailSyncError(
      e instanceof Error
        ? e.message
        : "Gmail sync failed. Please try again."
    );
  } finally {
    setSyncingGmail(false);
  }
};
  const stats = useMemo(() => {
    const total = leads.length;
    const hot = leads.filter((l) => (l.category || "").toLowerCase() === "hot").length;
    const pending = leads.filter((l) => l.email_status === "pending_approval").length;
    const sent = leads.filter((l) => l.email_status === "sent").length;
    return { total, hot, pending, sent };
  }, [leads]);

  const recent = useMemo(
    () =>
      [...leads]
        .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""))
        .slice(0, 6),
    [leads]
  );

  if (loading) return <LoadingSpinner label="Loading dashboard…" />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div>
      <div
  className="card"
  style={{
    marginBottom: 24,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
  }}
>
  <div>
    <div style={{ fontWeight: 700, fontSize: 15 }}>
      Gmail
    </div>

    <div
      style={{
        fontSize: 13,
        color: "var(--text-secondary)",
        marginTop: 4,
      }}
    >
      Check your inbox for new sales enquiries.
    </div>

    {gmailSyncMessage && (
      <div
        style={{
          fontSize: 13,
          marginTop: 8,
        }}
      >
        {gmailSyncMessage}
      </div>
    )}

    {gmailSyncError && (
      <div
        style={{
          fontSize: 13,
          marginTop: 8,
          color: "var(--danger, #c0392b)",
        }}
      >
        {gmailSyncError}
      </div>
    )}
  </div>

  <button
    className="btn btn-primary"
    onClick={handleGmailSync}
    disabled={syncingGmail}
  >
    {syncingGmail ? "Syncing Gmail..." : "Sync Gmail"}
  </button>
</div>
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-label"><Users size={14} /> Total Leads</div>
          <div className="stat-card-value">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label"><Flame size={14} /> Hot Leads</div>
          <div className="stat-card-value">{stats.hot}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label"><Clock size={14} /> Pending Approval</div>
          <div className="stat-card-value">{stats.pending}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label"><Send size={14} /> Emails Sent</div>
          <div className="stat-card-value">{stats.sent}</div>
        </div>
      </div>

      {stats.pending > 0 && (
        <div
          className="card"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            marginBottom: 24,
            background: "var(--warm-tint)",
            borderColor: "#F2D9A6",
          }}
        >
          <div>
            <div style={{ fontWeight: 700, fontSize: 14 }}>Needs Attention</div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              {stats.pending} email{stats.pending === 1 ? "" : "s"} waiting for approval
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/pending")}>
            Review Leads <ArrowRight size={15} />
          </button>
        </div>
      )}

      <div className="page-header">
        <h2>Recent Leads</h2>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate("/leads")}>
          View all
        </button>
      </div>

      {recent.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No leads yet"
          description="Add your first lead to see it show up here."
          action={
            <button className="btn btn-primary" onClick={() => navigate("/leads/new")}>
              Add your first lead
            </button>
          }
        />
      ) : (
        <LeadTable leads={recent} />
      )}
    </div>
  );
}
