export function Settings() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  return (
    <div style={{ maxWidth: 480 }}>
      <div className="page-header">
        <h2>Settings</h2>
      </div>
      <div className="card">
        <div className="card-title">Connection</div>
        <div className="kv-label">Backend API URL</div>
        <div className="kv-value tabular">{apiBaseUrl}</div>
        <p style={{ marginTop: 12, fontSize: 12.5, color: "var(--text-tertiary)" }}>
          Configured via the VITE_API_BASE_URL environment variable.
        </p>
      </div>
    </div>
  );
}
