import type {
  Lead,
  LeadInput,
  PipelineResponse,
} from "./types";

import { supabase } from "./lib/supabase";


// =========================================================
// API BASE URL
// =========================================================

const BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");


// =========================================================
// GENERIC AUTHENTICATED REQUEST
// =========================================================

async function req<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {

  const {
    data: {
      session,
    },
  } = await supabase.auth.getSession();


  const headers = new Headers(
    init.headers
  );

  headers.set(
    "Content-Type",
    "application/json"
  );


  if (session?.access_token) {

    headers.set(
      "Authorization",
      `Bearer ${session.access_token}`
    );

  }


  const response = await fetch(
    BASE + path,
    {
      ...init,
      headers,
    }
  );


  const data =
    await response
      .json()
      .catch(() => null);


  if (!response.ok) {

    throw new Error(
      data?.detail ||
      "Request failed. Please try again."
    );

  }


  return data;
}


// =========================================================
// LEADS
// =========================================================

export const getLeads =
  async (): Promise<Lead[]> => {

    const data =
      await req<{
        leads: Lead[];
      }>("/leads");

    return data.leads;
  };


export const getLead = (
  id: number
) =>
  req<Lead>(
    `/leads/${id}`
  );


export const createLead = (
  x: LeadInput
) =>
  req<PipelineResponse>(
    "/leads",
    {
      method: "POST",
      body: JSON.stringify(x),
    }
  );


// =========================================================
// EMAIL APPROVAL
// =========================================================

export const approveLead = (
  id: number
) =>
  req<{
    message: string;
    lead: Lead;
  }>(
    `/leads/${id}/approve`,
    {
      method: "POST",

      body: JSON.stringify({
        approved: true,
      }),
    }
  );


export const rejectLead = (
  id: number
) =>
  req<{
    message: string;
    lead: Lead;
  }>(
    `/leads/${id}/approve`,
    {
      method: "POST",

      body: JSON.stringify({
        approved: false,
      }),
    }
  );


// =========================================================
// EMAIL EDIT
// =========================================================

export const updateEmail = (
  id: number,
  subject: string,
  body: string
) =>
  req<Lead>(
    `/leads/${id}/email`,
    {
      method: "PATCH",

      body: JSON.stringify({
        subject,
        body,
      }),
    }
  );


// =========================================================
// SEND EMAIL
// =========================================================

export const sendLead = (
  id: number
) =>
  req(
    `/leads/${id}/send`,
    {
      method: "POST",
    }
  );


// =========================================================
// GMAIL STATUS
// =========================================================

export type GmailStatus = {
  connected: boolean;
  gmail_email: string | null;
};


export const getGmailStatus = () =>
  req<GmailStatus>(
    "/gmail/status"
  );


// =========================================================
// GMAIL DISCONNECT
// =========================================================

export const disconnectGmail = () =>
  req<{
    success: boolean;
    message: string;
  }>(
    "/gmail/disconnect",
    {
      method: "DELETE",
    }
  );


// =========================================================
// GMAIL SYNC
// =========================================================

export const syncGmail = () =>
  req<{
    success: boolean;
    messages_checked: number;
    leads_created: number;
    duplicates_skipped: number;
    non_leads_skipped: number;
    created_leads?: Lead[];
    processed_leads?: unknown[];
    failed_leads?: unknown[];
  }>(
    "/gmail/sync",
    {
      method: "POST",
    }
  );