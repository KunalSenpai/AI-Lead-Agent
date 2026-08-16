import type { Lead } from "../../types/lead";

interface AnalysisCardProps {
  lead: Lead;
}

export function AnalysisCard({ lead }: AnalysisCardProps) {
  return (
    <div className="card">
      <div className="card-title">AI Analysis</div>
      <div className="kv-grid">
        <div>
          <div className="kv-label">Industry</div>
          <div className="kv-value">{lead.industry || "—"}</div>
        </div>
        <div>
          <div className="kv-label">Company Size</div>
          <div className="kv-value">
            {lead.company_size != null ? `${lead.company_size} employees` : "—"}
          </div>
        </div>
        <div>
          <div className="kv-label">Lead Volume</div>
          <div className="kv-value">
            {lead.lead_volume != null ? `${lead.lead_volume}/month` : "—"}
          </div>
        </div>
        <div>
          <div className="kv-label">Urgency</div>
          <div className="kv-value" style={{ textTransform: "capitalize" }}>
            {lead.urgency || "—"}
          </div>
        </div>
      </div>
      {lead.problem && (
        <div style={{ marginTop: 14 }}>
          <div className="kv-label">Problem</div>
          <div className="kv-value">{lead.problem}</div>
        </div>
      )}
    </div>
  );
}
