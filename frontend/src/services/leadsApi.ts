import type {
  Lead,
  LeadInput,
  PipelineResponse,
  EmailEditInput,
  LeadActionResponse,
  SendResponse,
} from "../types/lead";

import { supabase } from "../lib/supabase";


// =========================================================
// API CONFIGURATION
// =========================================================

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");


// =========================================================
// API ERROR
// =========================================================

export class ApiError extends Error {
  status: number;

  constructor(
    message: string,
    status: number
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
  }
}


// =========================================================
// GENERIC AUTHENTICATED REQUEST
// =========================================================

async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {

  let response: Response;

  try {

    // -----------------------------------------------------
    // Get current Supabase session
    // -----------------------------------------------------

    const {
      data: {
        session,
      },
    } = await supabase.auth.getSession();

    const accessToken =
      session?.access_token;


    // -----------------------------------------------------
    // Require authentication
    // -----------------------------------------------------

    if (!accessToken) {

      throw new ApiError(
        "You are not authenticated. Please sign in again.",
        401
      );

    }


    // -----------------------------------------------------
    // Build headers
    // -----------------------------------------------------

    const headers = new Headers(
      init.headers
    );

    headers.set(
      "Content-Type",
      "application/json"
    );

    headers.set(
      "Authorization",
      `Bearer ${accessToken}`
    );


    // -----------------------------------------------------
    // Send request
    // -----------------------------------------------------

    response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...init,
        headers,
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


  // =======================================================
  // Parse response
  // =======================================================

  const isJson =
    response.headers
      .get("content-type")
      ?.includes("application/json");


  const data = isJson
    ? await response
        .json()
        .catch(() => null)
    : null;


  // =======================================================
  // Handle API errors
  // =======================================================

  if (!response.ok) {

    let detail =
      "Something went wrong. Please try again.";


    if (
      data &&
      typeof data.detail === "string"
    ) {

      detail = data.detail;

    } else if (
      data &&
      Array.isArray(data.detail)
    ) {

      // FastAPI validation errors
      detail =
        data.detail
          .map(
            (item: {
              msg?: string;
            }) =>
              item?.msg || "Validation error"
          )
          .join(", ");

    }


    throw new ApiError(
      detail,
      response.status
    );
  }


  return data as T;
}


// =========================================================
// LEADS
// =========================================================


// ---------------------------------------------------------
// Get single lead
// ---------------------------------------------------------

export async function getLead(
  id: number
): Promise<Lead> {

  const data =
    await request<{
      lead: Lead;
    }>(
      `/leads/${id}`
    );

  return data.lead;
}


// ---------------------------------------------------------
// Get leads
// ---------------------------------------------------------

export async function getLeads(
  status?: string
): Promise<Lead[]> {

  const query = status
    ? `?status=${encodeURIComponent(status)}`
    : "";


  const data =
    await request<{
      leads: Lead[];
    }>(
      `/leads${query}`
    );


  return data.leads;
}


// ---------------------------------------------------------
// Create lead
// ---------------------------------------------------------

export function createLead(
  input: LeadInput
): Promise<PipelineResponse> {

  return request<PipelineResponse>(
    "/leads",
    {
      method: "POST",

      body: JSON.stringify(
        input
      ),
    }
  );
}


// =========================================================
// APPROVE EMAIL
// =========================================================
//
// Backend:
//
// POST /leads/{lead_id}/approve
//
// Required body:
//
// {
//   "approved": true
// }
//
// =========================================================

export function approveLead(
  id: number
): Promise<LeadActionResponse> {

  return request<LeadActionResponse>(
    `/leads/${id}/approve`,
    {
      method: "POST",

      body: JSON.stringify({
        approved: true,
      }),
    }
  );
}


// =========================================================
// REJECT EMAIL
// =========================================================
//
// Backend:
//
// POST /leads/{lead_id}/approve
//
// Required body:
//
// {
//   "approved": false
// }
//
// =========================================================

export function rejectLead(
  id: number
): Promise<LeadActionResponse> {

  return request<LeadActionResponse>(
    `/leads/${id}/approve`,
    {
      method: "POST",

      body: JSON.stringify({
        approved: false,
      }),
    }
  );
}


// =========================================================
// UPDATE EMAIL
// =========================================================
//
// Backend:
//
// PATCH /leads/{lead_id}/email
//
// =========================================================

export function updateEmail(
  id: number,
  input: EmailEditInput
): Promise<LeadActionResponse> {

  return request<LeadActionResponse>(
    `/leads/${id}/email`,
    {
      method: "PATCH",

      body: JSON.stringify(
        input
      ),
    }
  );
}


// =========================================================
// SEND EMAIL
// =========================================================

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


// =========================================================
// GMAIL
// =========================================================

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


// ---------------------------------------------------------
// Gmail sync
// ---------------------------------------------------------

export function syncGmail():
  Promise<GmailSyncResponse> {

  return request<GmailSyncResponse>(
    "/gmail/sync",
    {
      method: "POST",
    }
  );
}