import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createLead, ApiError } from "../services/leadsApi";
import type { LeadInput } from "../types/lead";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

const EMPTY: LeadInput = { name: "", email: "", company: "", website: "", job_title: "", message: "" };

export function AddLead() {
  const navigate = useNavigate();
  const [form, setForm] = useState<LeadInput>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof LeadInput, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function update<K extends keyof LeadInput>(key: K, value: LeadInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function validate(): boolean {
    const next: Partial<Record<keyof LeadInput, string>> = {};
    if (!form.name.trim()) next.name = "Name is required.";
    if (!form.email.trim()) next.email = "Email is required.";
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = "Enter a valid email address.";
    if (!form.company.trim()) next.company = "Company is required.";
    if (!form.message.trim()) next.message = "Message is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload: LeadInput = {
        ...form,
        website: form.website?.trim() || undefined,
        job_title: form.job_title?.trim() || undefined,
      };
      const result = await createLead(payload);
      navigate(`/leads/${result.lead.id}`);
    } catch (e) {
      setSubmitError(
        e instanceof ApiError
          ? e.message
          : "Something went wrong while analyzing this lead. Please try again."
      );
      setSubmitting(false);
    }
  }

  if (submitting) {
    return (
      <div className="card" style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
        <LoadingSpinner label="Analyzing lead and preparing recommendation…" />
        <p style={{ color: "var(--text-tertiary)", fontSize: 12.5, marginTop: 8 }}>
          This can take a little while — the assistant is researching the company and drafting an email.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <div className="page-header">
        <h2>Add Lead</h2>
      </div>

      <form className="card" onSubmit={handleSubmit} noValidate>
        {submitError && (
          <div style={{ marginBottom: 18 }}>
            <p role="alert" className="field-error" style={{ fontSize: 13.5 }}>{submitError}</p>
          </div>
        )}

        <div className="field">
          <label htmlFor="lead-name">Name</label>
          <input
            id="lead-name"
            className={`input ${errors.name ? "input-error" : ""}`}
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Daniel Brooks"
            aria-invalid={!!errors.name}
          />
          {errors.name && <span className="field-error">{errors.name}</span>}
        </div>

        <div className="field">
          <label htmlFor="lead-email">Email</label>
          <input
            id="lead-email"
            type="email"
            className={`input ${errors.email ? "input-error" : ""}`}
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            placeholder="daniel@northstar.example"
            aria-invalid={!!errors.email}
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="field">
          <label htmlFor="lead-company">Company</label>
          <input
            id="lead-company"
            className={`input ${errors.company ? "input-error" : ""}`}
            value={form.company}
            onChange={(e) => update("company", e.target.value)}
            placeholder="Northstar Logistics"
            aria-invalid={!!errors.company}
          />
          {errors.company && <span className="field-error">{errors.company}</span>}
        </div>

        <div className="field">
          <label htmlFor="lead-website">Website</label>
          <input
            id="lead-website"
            className="input"
            value={form.website}
            onChange={(e) => update("website", e.target.value)}
            placeholder="https://northstar.example"
          />
          <span className="field-hint">Used for AI company research — recommended if you have it.</span>
        </div>

        <div className="field">
          <label htmlFor="lead-title">Job Title</label>
          <input
            id="lead-title"
            className="input"
            value={form.job_title}
            onChange={(e) => update("job_title", e.target.value)}
            placeholder="VP of Sales"
          />
        </div>

        <div className="field" style={{ marginBottom: 8 }}>
          <label htmlFor="lead-message">Message</label>
          <textarea
            id="lead-message"
            className={`textarea ${errors.message ? "input-error" : ""}`}
            value={form.message}
            onChange={(e) => update("message", e.target.value)}
            placeholder="What did this prospect say or ask about?"
            aria-invalid={!!errors.message}
          />
          {errors.message && <span className="field-error">{errors.message}</span>}
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: 10 }}>
          Analyze Lead
        </button>
      </form>
    </div>
  );
}
