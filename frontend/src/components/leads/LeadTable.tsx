import { useNavigate } from "react-router-dom";
import type { Lead } from "../../types/lead";
import { ScoreBadge } from "../ui/ScoreBadge";
import { StatusBadge } from "../ui/StatusBadge";
import { formatDate } from "../../utils/format";

interface LeadTableProps {
  leads: Lead[];
}

export function LeadTable({ leads }: LeadTableProps) {
  const navigate = useNavigate();

  return (
    <div className="table-wrap responsive">
      <table className="lead-table">
        <thead>
          <tr>
            <th>Lead</th>
            <th>Company</th>
            <th>Score</th>
            <th>Category</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr
              key={lead.id}
              tabIndex={0}
              onClick={() => navigate(`/leads/${lead.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") navigate(`/leads/${lead.id}`);
              }}
              aria-label={`View lead ${lead.name} at ${lead.company}`}
            >
              <td data-label="Lead">
                <div className="lead-name">{lead.name}</div>
                <div className="lead-sub">{lead.email}</div>
              </td>
              <td data-label="Company">{lead.company}</td>
              <td data-label="Score" className="tabular">
                {lead.score ?? "—"}
              </td>
              <td data-label="Category">
                <ScoreBadge category={lead.category} />
              </td>
              <td data-label="Status">
                <StatusBadge status={lead.email_status} />
              </td>
              <td data-label="Date" className="lead-sub">
                {formatDate(lead.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
