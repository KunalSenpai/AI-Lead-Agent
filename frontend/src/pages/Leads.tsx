import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Plus, Users } from "lucide-react";
import { useLeads } from "../hooks/useLeads";
import { LeadTable } from "../components/leads/LeadTable";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "Hot", label: "Hot" },
  { key: "Warm", label: "Warm" },
  { key: "Cold", label: "Cold" },
  { key: "pending_approval", label: "Pending Approval" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "sent", label: "Sent" },
];

const CATEGORY_FILTERS = new Set(["Hot", "Warm", "Cold"]);

export function Leads() {
  const { leads, loading, error, reload } = useLeads();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    let result = leads;

    if (filter !== "all") {
      result = CATEGORY_FILTERS.has(filter)
        ? result.filter((l) => l.category === filter)
        : result.filter((l) => l.email_status === filter);
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(
        (l) =>
          l.name.toLowerCase().includes(q) ||
          l.company.toLowerCase().includes(q) ||
          l.email.toLowerCase().includes(q)
      );
    }

    return result;
  }, [leads, filter, search]);

  return (
    <div>
      <div className="page-header">
        <h2>Leads</h2>
        <button className="btn btn-primary" onClick={() => navigate("/leads/new")}>
          <Plus size={16} /> Add Lead
        </button>
      </div>

      <div className="search-input-wrap">
        <Search size={15} />
        <input
          className="input"
          placeholder="Search leads, companies, emails…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search leads"
        />
      </div>

      <div className="filter-row" role="group" aria-label="Filter leads">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={`filter-pill ${filter === f.key ? "filter-pill-active" : ""}`}
            onClick={() => setFilter(f.key)}
            aria-pressed={filter === f.key}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner label="Loading leads…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={reload} />
      ) : filtered.length === 0 ? (
        leads.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No leads yet"
            description="Add your first lead to start the AI qualification pipeline."
            action={
              <button className="btn btn-primary" onClick={() => navigate("/leads/new")}>
                Add your first lead
              </button>
            }
          />
        ) : (
          <EmptyState icon={Search} title="No matching leads" description="Try a different search or filter." />
        )
      ) : (
        <LeadTable leads={filtered} />
      )}
    </div>
  );
}
