# AI Lead Agent

An AI-powered lead management and sales automation platform that turns inbound enquiries into researched, scored, and personalized sales opportunities.

## Features

- 🔐 User authentication with Supabase
- 👤 User-isolated lead data with Supabase RLS
- 🤖 AI-powered lead analysis and scoring
- 🔎 Automated company research
- ✉️ AI-generated personalized sales emails
- 👀 Human approval workflow before sending
- 📧 Gmail OAuth integration
- 🔄 Gmail inbox synchronization
- 🛡️ Duplicate email-send protection
- ⚡ FastAPI backend + React frontend

## Workflow

```text
Lead
  ↓
AI Analysis
  ↓
Company Research
  ↓
Lead Scoring
  ↓
Email Generation
  ↓
Human Approval
  ↓
Gmail
  ↓
Sent

Tech Stack

Frontend

React
TypeScript
Vite

Backend

Python
FastAPI
Pydantic

AI

Google Gemini

Database & Auth

Supabase
PostgreSQL
Supabase Auth
Row Level Security

Integrations

Gmail API
Google OAuth

Deployment

Vercel — frontend
Render — backend
Production

Frontend:
https://ai-lead-agent-phi.vercel.app/

Backend:
https://ai-lead-agent-kibe.onrender.com/

Local Development
Backend
git clone <repository-url>
cd AI-Agent


python -m venv .venv

Activate the environment:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Configure .env with your Supabase, Gemini, and Google OAuth credentials.

Start the backend:

uvicorn app.main:app --reload
Frontend
cd frontend
npm install
npm run dev
Testing

Run the application test suite:

pytest -q --ignore=test_genai.py

The current application suite passes 68 tests.

test_genai.py performs a live Gemini API request and may be affected by external API/network availability.

Security
Authenticated API access
User-scoped database queries
Supabase service-role operations restricted to the backend
Gmail OAuth for user mailbox access
No credentials committed to source control

Project Goal

Built as a portfolio project demonstrating practical application of AI agents, SaaS authentication, multi-user data isolation, OAuth integrations, automated research, lead scoring, and sales workflow automation.

