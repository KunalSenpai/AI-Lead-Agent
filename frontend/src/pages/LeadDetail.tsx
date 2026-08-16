import { useParams, useNavigate } from "react-router-dom";
import { Globe, Mail, Briefcase } from "lucide-react";
import { useLead } from "../hooks/useLead";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { LeadScoreCard } from "../components/leads/LeadScoreCard";
import { AnalysisCard } from "../components/leads/AnalysisCard";
import { ResearchCard } from "../components/leads/ResearchCard";
import { EmailDraftCard } from "../components/leads/EmailDraftCard";

export function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const leadId = Number(id);
  const { lead, setLead, loading, error, reload } = useLead(leadId);

  if (!id || Number.isNaN(leadId)) {
    return <ErrorMessage message="Invalid lead." />;
  }

  if (loading) return <LoadingSpinner label="Loading lead…" />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!lead) return <ErrorMessage message="This lead could not be found." />;

  return (
    <div>
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => navigate("/leads")}
        style={{ marginBottom: 14 }}
      >
        ← Back to leads
      </button>

      <div className="detail-header">
        <div>
          <h2 style={{ fontSize: 22 }}>{lead.company}</h2>
          <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 3 }}>
            <div style={{ fontWeight: 600, fontSize: 14.5 }}>{lead.name}</div>
            {lead.job_title && (
              <div style={{ fontSize: 13, color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 5 }}>
                <Briefcase size={13} /> {lead.job_title}
              </div>
            )}
            <div style={{ fontSize: 13, color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 5 }}>
              <Mail size={13} /> {lead.email}
            </div>
            {lead.website && (
              <a
                href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: 13, color: "var(--brand)", display: "flex", alignItems: "center", gap: 5 }}
              >
                <Globe size={13} /> {lead.website}
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="stack">
          <LeadScoreCard lead={lead} />

          <div className="card">
            <div className="card-title">Lead Information</div>
            <div className="kv-label" style={{ marginBottom: 6 }}>Original Message</div>
            <div className="kv-value" style={{ whiteSpace: "pre-wrap" }}>{lead.message}</div>
          </div>

          <AnalysisCard lead={lead} />
          <ResearchCard lead={lead} />
        </div>

        <div className="stack">
          <EmailDraftCard lead={lead} onLeadUpdate={setLead} />
        </div>
      </div>
    </div>
  );
}
