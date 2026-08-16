import { useState } from "react";

interface EmailEditorProps {
  initialSubject: string;
  initialBody: string;
  saving: boolean;
  onCancel: () => void;
  onSave: (subject: string, body: string) => void;
}

export function EmailEditor({ initialSubject, initialBody, saving, onCancel, onSave }: EmailEditorProps) {
  const [subject, setSubject] = useState(initialSubject);
  const [body, setBody] = useState(initialBody);
  const [error, setError] = useState<string | null>(null);

  function handleSave() {
    if (!subject.trim() || !body.trim()) {
      setError("Subject and body can't be empty.");
      return;
    }
    setError(null);
    onSave(subject.trim(), body);
  }

  return (
    <div className="stack">
      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="email-subject">Subject</label>
        <input
          id="email-subject"
          className="input"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={saving}
        />
      </div>
      <div className="field" style={{ marginBottom: 0 }}>
        <label htmlFor="email-body">Body</label>
        <textarea
          id="email-body"
          className="textarea"
          style={{ minHeight: 220 }}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={saving}
        />
      </div>
      {error && <p className="field-error">{error}</p>}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button className="btn btn-secondary" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save Changes"}
        </button>
      </div>
    </div>
  );
}
