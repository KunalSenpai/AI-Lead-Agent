import { useMemo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { useLeads } from "../hooks/useLeads";
import { LeadCard } from "../components/leads/LeadCard";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";

type SortKey = "newest" | "score";

export function Pending() {
  const { leads, loading, error, reload } = useLeads("pending_approval");
  const [sort, setSort] = useState<SortKey>("score");

  const pending = useMemo(() => {
    const list = leads.filter((l) => l.email_status === "pending_approval");
    return [...list].sort((a, b) =>
      sort === "score"
        ? (b.score ?? 0) - (a.score ?? 0)
        : (b.created_at || "").localeCompare(a.created_at || "")
    );
  }, [leads, sort]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Pending Approval</h2>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
            {pending.length} email{pending.length === 1 ? "" : "s"} waiting for review
          </p>
        </div>
        <div className="filter-row" style={{ marginBottom: 0 }}>
          <button
            className={`filter-pill ${sort === "score" ? "filter-pill-active" : ""}`}
            onClick={() => setSort("score")}
          >
            Highest score
          </button>
          <button
            className={`filter-pill ${sort === "newest" ? "filter-pill-active" : ""}`}
            onClick={() => setSort("newest")}
          >
            Newest
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="Loading pending emails…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={reload} />
      ) : pending.length === 0 ? (
        <EmptyState icon={CheckCircle2} title="You're all caught up" description="No emails are waiting for approval right now." />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
          {pending.map((lead) => (
            <LeadCard key={lead.id} lead={lead} />
          ))}
        </div>
      )}
    </div>
  );
}
