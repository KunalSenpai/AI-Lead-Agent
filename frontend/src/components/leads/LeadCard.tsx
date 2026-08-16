import { useNavigate } from "react-router-dom";
import type { Lead } from "../../types/lead";
import { ScoreBadge } from "../ui/ScoreBadge";
import { StatusBadge } from "../ui/StatusBadge";

interface LeadCardProps {
  lead: Lead;
}

// Used on Pending / mobile-friendly review surfaces where a single lead
// needs to be scanned quickly with a clear call to action.
export function LeadCard({ lead }: LeadCardProps) {
  const navigate = useNavigate();

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14.5 }}>{lead.name}</div>
          <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>{lead.company}</div>
          {lead.job_title && (
            <div style={{ color: "var(--text-tertiary)", fontSize: 12 }}>{lead.job_title}</div>
          )}
        </div>
        <ScoreBadge category={lead.category} score={lead.score} size="md" />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <StatusBadge status={lead.email_status} />
        <button className="btn btn-primary btn-sm" onClick={() => navigate(`/leads/${lead.id}`)}>
          Review
        </button>
      </div>
    </div>
  );
}
