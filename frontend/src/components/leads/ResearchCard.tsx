import type { Lead } from "../../types/lead";

interface ResearchCardProps {
  lead: Lead;
}

export function ResearchCard({ lead }: ResearchCardProps) {
  const research = lead.research_data;

  if (!research) {
    return (
      <div className="card">
        <div className="card-title">Company Research</div>
        <p style={{ color: "var(--text-tertiary)", fontSize: 13.5 }}>
          No research available for this lead yet.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Company Research</div>
      <div className="stack">
        <div className="kv-grid">
          <div>
            <div className="kv-label">Company</div>
            <div className="kv-value">{research.company_name}</div>
          </div>
          <div>
            <div className="kv-label">Industry</div>
            <div className="kv-value">{research.industry || "—"}</div>
          </div>
          <div>
            <div className="kv-label">Target Customers</div>
            <div className="kv-value">{research.target_customers || "—"}</div>
          </div>
          <div>
            <div className="kv-label">Company Size</div>
            <div className="kv-value">
              {research.company_size != null ? `${research.company_size} employees` : "—"}
            </div>
          </div>
        </div>

        <div>
          <div className="kv-label">Description</div>
          <div className="kv-value">{research.description}</div>
        </div>

        {research.products_or_services?.length > 0 && (
          <div>
            <div className="kv-label" style={{ marginBottom: 6 }}>Products / Services</div>
            <div className="chip-list">
              {research.products_or_services.map((p, i) => (
                <span className="chip" key={i}>{p}</span>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="kv-label">Summary</div>
          <div className="kv-value">{research.summary}</div>
        </div>

        {research.source_urls?.length > 0 && (
          <div>
            <div className="kv-label" style={{ marginBottom: 6 }}>Sources</div>
            <ul className="link-list">
              {research.source_urls.map((url, i) => (
                <li key={i}>
                  <a href={url} target="_blank" rel="noreferrer" style={{ color: "var(--brand)", fontSize: 13 }}>
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
