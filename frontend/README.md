# AI Lead Agent — Frontend

React + TypeScript + Vite frontend for the existing FastAPI backend in
`KunalSenpai/AI-Lead-Agent`. Built by inspecting the actual backend code
(`app/api/leads.py`, `app/models/lead.py`, `app/tools/database.py`) rather
than guessing — every request/response shape in `src/types/lead.ts` and
`src/services/leadsApi.ts` matches the real backend, except one endpoint
noted below that doesn't exist in the backend yet.

## ⚠️ One backend dependency: `GET /leads`

The existing backend only has `GET /leads/{id}` — there is no way to list
leads. The Dashboard, Leads, Pending, and Sent pages all need a list
endpoint, so the frontend is built assuming this contract:

```
GET /leads
GET /leads?status=<email_status>   (optional filter)

→ 200 OK
[
  { ...same flat lead row shape as GET /leads/{id}'s "lead" object... },
  ...
]
```

Notes on the contract this frontend expects:
- Returns a **JSON array** of lead rows directly (not wrapped in `{ "leads": [...] }`).
- Each row has the exact same fields as the `lead` object inside the
  existing `GET /leads/{id}` response (see `app/tools/database.py` —
  it's the raw Supabase `leads` table row).
- The optional `status` query param, if you choose to support it, should
  filter on `email_status`. The frontend also works fine if you only
  implement the no-filter version — it filters client-side as a fallback
  (see `src/hooks/useLeads.ts` / `src/pages/Leads.tsx`).

A minimal implementation consistent with the existing code style:

```python
# app/tools/database.py
def list_leads(status: str | None = None):
    query = supabase.table("leads").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("email_status", status)
    response = query.execute()
    return response.data or []

# app/api/leads.py
@router.get("/leads")
def get_leads(status: str | None = None):
    return list_leads(status)
```

If your actual implementation returns a different shape (e.g. wrapped in
an object, paginated, etc.), the only file that needs to change is
`src/services/leadsApi.ts` — `getLeads()`.

## Verified endpoints used (all real, from `app/api/leads.py`)

| Method | Path | Notes |
|---|---|---|
| `POST` | `/leads` | Runs full pipeline; can take several seconds |
| `GET` | `/leads/{id}` | Returns `{ lead: {...} }` |
| `POST` | `/leads/{id}/approve` | No body; 400 unless status is `pending_approval` |
| `POST` | `/leads/{id}/reject` | No body; 400 unless status is `pending_approval` |
| `PUT` | `/leads/{id}/email` | Body `{subject, body}`; resets status to `pending_approval` |
| `POST` | `/leads/{id}/send` | No body; 400 unless status is `approved`; blocks duplicate sends |

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # then edit VITE_API_BASE_URL if needed
npm run dev
```

Backend must be running separately (`uvicorn app.main:app --reload --port 8000`).

## Structure

```
src/
├── components/
│   ├── layout/     AppShell, Sidebar, Topbar
│   ├── ui/         ScoreBadge, StatusBadge, LoadingSpinner, EmptyState,
│   │                ErrorMessage, ConfirmDialog, Toast
│   └── leads/       LeadTable, LeadCard, LeadScoreCard, AnalysisCard,
│                    ResearchCard, EmailDraftCard, EmailEditor, ApprovalActions
├── pages/          Dashboard, Leads, AddLead, LeadDetail, Pending, Sent, Settings
├── services/       leadsApi.ts — the only file that calls fetch()
├── hooks/          useLeads, useLead
├── types/          lead.ts — mirrors the backend's Pydantic/Supabase shapes
├── utils/          format.ts, statusLabels.ts
├── App.tsx, main.tsx, index.css
```

## What's intentionally NOT here

No lead scoring, no Hot/Warm/Cold logic, no approval-safety logic, no
Gmail/Gemini calls. All business rules stay server-side — the frontend
only renders what the backend returns and calls the backend's real
approve/reject/edit/send endpoints, which remain the final authority.

Verified with `npx tsc -b` (0 errors) and `npx vite build` (succeeds).
