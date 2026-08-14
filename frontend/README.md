# AI Lead Agent Frontend

React + TypeScript + Vite UI for the existing FastAPI backend.

## Start

```powershell
npm install
copy .env.example .env
npm run dev
```

The frontend talks to FastAPI only. Gemini, Gmail and Supabase remain backend responsibilities.

Known routes used:
- GET /leads
- GET /leads/{id}
- POST /leads
- POST /leads/{id}/approve
- POST /leads/{id}/send

Reject currently sends `{ "approved": false }` to the approval route. If your backend has a dedicated reject endpoint, change `rejectLead()` in `src/api.ts`.
