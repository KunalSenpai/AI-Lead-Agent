// Types mirror the backend's flat `leads` table row exactly
// (see app/tools/database.py and app/models/lead.py in the FastAPI backend).
// The backend is the source of truth for shape and values — nothing here
// is invented; unions are left as `string` where the backend does not
// constrain the value to a fixed enum in code.

export type EmailStatus = "pending_approval" | "approved" | "rejected" | "sent";

export interface CompanyResearch {
  company_name: string;
  industry: string | null;
  description: string;
  products_or_services: string[];
  target_customers: string | null;
  company_size: number | null;
  summary: string;
  source_urls: string[];
}

export interface LeadAnalysis {
  industry: string;
  company_size: number | null;
  lead_volume: number | null;
  problem: string;
  urgency: string;
}

export interface LeadScore {
  score: number;
  category: string; // "Hot" | "Warm" | "Cold" as returned by the backend
  reasons: string[];
}

export interface EmailDraft {
  subject: string;
  body: string;
}

// The flat lead row as returned by GET /leads, GET /leads/{id}, and
// embedded in every mutation response.
export interface Lead {
  id: number;
  name: string;
  email: string;
  company: string;
  website: string | null;
  job_title: string | null;
  message: string;
  created_at: string | null;

  // AI analysis
  industry: string | null;
  company_size: number | null;
  lead_volume: number | null;
  problem: string | null;
  urgency: string | null;

  // Lead score
  score: number | null;
  category: string | null;
  score_reasons: string[] | null;

  // Company research
  research_summary: string | null;
  research_data: CompanyResearch | null;
  research_sources: string[] | null;

  // Email draft / workflow
  email_subject: string | null;
  email_body: string | null;
  email_status: EmailStatus | null;
  sent_at: string | null;
}

// POST /leads request body
export interface LeadInput {
  name: string;
  email: string;
  company: string;
  website?: string;
  job_title?: string;
  message: string;
}

// POST /leads response body
export interface PipelineResponse {
  lead: Lead;
  analysis: LeadAnalysis;
  score: LeadScore;
  research: CompanyResearch;
  email: EmailDraft;
}

// PUT /leads/{id}/email request body
export interface EmailEditInput {
  subject: string;
  body: string;
}

// Generic { message, lead } response shape used by
// approve / reject / edit-email
export interface LeadActionResponse {
  message: string;
  lead: Lead;
}

// POST /leads/{id}/send response body
export interface SendResponse {
  message: string;
  gmail_message_id: string;
  lead: Lead;
}
