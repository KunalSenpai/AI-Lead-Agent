import type {
  Lead,
  LeadInput,
  PipelineResponse,
  EmailEditInput,
  LeadActionResponse,
  SendResponse,
} from "../types/lead";

import { supabase } from "../lib/supabase";

// Only public, non-secret config belongs in VITE_ variables.
// This is the sole place in the app that knows the backend's base URL.
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(
    message: string,
    status: number
  ) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  let response: Response;

  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const accessToken = session?.access_token;

    if (!accessToken) {
      throw new ApiError(
        "You are not authenticated. Please sign in again.",
        401
      );
    }

    response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...init,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          ...(init.headers || {}),
        },
      }
    );
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(
      "Can't reach the server. Check your connection and try again.",
      0
    );
  }

  const isJson = response.headers
    .get("content-type")
    ?.includes("application/json");

  const data = isJson
    ? await response.json().catch(() => null)
    : null;

  if (!response.ok) {
    const detail =
      (data &&
        typeof data.detail === "string" &&
        data.detail) ||
      "Something went wrong. Please try again.";

    throw new ApiError(
      detail,
      response.status
    );
  }

  return data as T;
}

// ---------------------------------------------------------------------
// Leads
// ---------------------------------------------------------------------

export async function getLead(
  id: number
): Promise<Lead> {
  const data = await request<{ lead: Lead }>(
    `/leads/${id}`
  );

  return data.lead;
}

export async function getLeads(
  status?: string
): Promise<Lead[]> {
  const query = status
    ? `?status=${encodeURIComponent(status)}`
    : "";

  const data = await request<{ leads: Lead[] }>(
    `/leads${query}`
  );

  return data.leads;
}

export function createLead(
  input: LeadInput
): Promise<PipelineResponse> {
  return request<PipelineResponse>(
    "/leads",
    {
      method: "POST",
      body: JSON.stringify(input),
    }
  );
}

export function approveLead(
  id: number
): Promise<LeadActionResponse> {
  return request<LeadActionResponse>(
    `/leads/${id}/approve`,
    {
      method: "POST",
    }
  );
}

export function rejectLead(
  id: number
): Promise<LeadActionResponse> {
  return request<LeadActionResponse>(
    `/leads/${id}/reject`,
    {
      method: "POST",
    }
  );
}

export function updateEmail(
  id: number,
  input: EmailEditInput
): Promise<LeadActionResponse> {
  return request<LeadActionResponse>(
    `/leads/${id}/email`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    }
  );
}

export function sendLeadEmail(
  id: number
): Promise<SendResponse> {
  return request<SendResponse>(
    `/leads/${id}/send`,
    {
      method: "POST",
    }
  );
}

// ---------------------------------------------------------------------
// Gmail
// ---------------------------------------------------------------------

export interface GmailSyncResponse {
  success: boolean;
  messages_checked: number;
  leads_created: number;
  duplicates_skipped: number;
  non_leads_skipped: number;
  processed_leads: Lead[];
  failed_leads: {
    lead_id: number;
    error: string;
  }[];
}

export function syncGmail(): Promise<GmailSyncResponse> {
  return request<GmailSyncResponse>(
    "/gmail/sync",
    {
      method: "POST",
    }
  );
}