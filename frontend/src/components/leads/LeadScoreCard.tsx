import { CheckCircle2 } from "lucide-react";
import type { Lead } from "../../types/lead";
import { ScoreBadge } from "../ui/ScoreBadge";

interface LeadScoreCardProps {
  lead: Lead;
}

// The signature visual element for this app: a bold tabular-mono score
// paired with the backend's own reasons — never recomputed here.
export function LeadScoreCard({ lead }: LeadScoreCardProps) {
  const hasScore = typeof lead.score === "number";

  return (
    <div className="card">
      <div className="score-gauge" style={{ marginBottom: 18 }}>
        <div>
          <span className="score-gauge-value tabular">{hasScore ? lead.score : "—"}</span>
          <span className="score-gauge-max"> / 100</span>
        </div>
        <ScoreBadge category={lead.category} size="md" />
      </div>

      {lead.score_reasons && lead.score_reasons.length > 0 && (
        <>
          <div className="card-title" style={{ marginBottom: 10 }}>Why this lead?</div>
          <ul className="reason-list">
            {lead.score_reasons.map((reason, i) => (
              <li key={i}>
                <CheckCircle2 size={16} color="var(--success)" style={{ flexShrink: 0, marginTop: 1 }} />
                {reason}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
