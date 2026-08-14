# AI Lead Agent

AI-powered lead qualification and outreach system with a FastAPI backend and a React frontend.

The system is designed so that a normal user does **not** need to work with FastAPI endpoints or JSON manually. Leads can be entered through the web interface, processed by the backend, reviewed, approved, and emailed from the UI.

---

## Features

### Lead intake
- Add new leads from a simple web form.
- Capture:
  - Name
  - Email
  - Company
  - Website
  - Job title
  - Lead message

### AI lead analysis
The system uses Gemini to analyze incoming leads and extract:
- Industry
- Company size
- Lead volume
- Business problem
- Urgency

### Lead scoring
Leads receive:
- Score out of 100
- Category such as Hot, Warm, or Cold
- Reasons explaining the score

### Company research
The system researches the supplied company website and generates:
- Industry
- Description
- Products/services
- Target customers
- Approximate company size
- Business summary
- Source URLs

### AI email generation
The system generates a personalized outreach email containing:
- Subject
- Email body

### Human approval workflow
Emails are **not automatically sent**.

The workflow is:

```text
Lead created
    ↓
AI analysis
    ↓
Lead scoring
    ↓
Company research
    ↓
Email draft
    ↓
Pending approval
    ↓
Approve / Edit / Reject
    ↓
Send
```

### Gmail integration
Approved emails can be sent through the Gmail API.

### Supabase persistence
Lead information and workflow state are stored in Supabase.

### Logging
The backend records important events such as:
- Lead creation
- AI analysis
- Scoring
- Company research
- Email generation
- Approval
- Rejection
- Email sending
- Errors/retries

### Error handling
The backend includes retry handling for Gemini lead analysis and protects email state so a failed Gmail request does not incorrectly mark an email as sent.

---

# Architecture

```text
                         ┌─────────────────────┐
                         │       Browser       │
                         │   React Frontend    │
                         │    localhost:5173   │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP / JSON
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         │    localhost:8000  │
                         └──────┬───┬───┬──────┘
                                │   │   │
                    ┌───────────┘   │   └────────────┐
                    ▼               ▼                ▼
              ┌──────────┐   ┌──────────┐     ┌──────────┐
              │  Gemini  │   │ Supabase │     │  Gmail   │
              │   AI     │   │ Database │     │   API    │
              └──────────┘   └──────────┘     └──────────┘
```

---

# Project Structure

A typical project layout is:

```text
AI Lead Agent/
│
├── app/
│   ├── agents/
│   │   └── lead_agent.py
│   │
│   ├── api/
│   │   └── leads.py
│   │
│   ├── models/
│   │   └── lead.py
│   │
│   ├── services/
│   │   └── scoring.py
│   │
│   ├── tools/
│   │   ├── email.py
│   │   ├── gmail.py
│   │   └── research.py
│   │
│   └── main.py
│
├── tests/
│   ├── test_email.py
│   ├── test_email_workflow.py
│   ├── test_gmail.py
│   ├── test_lead_agent.py
│   ├── test_lead_pipeline.py
│   ├── test_research.py
│   └── test_scoring.py
│
├── credentials/
│   └── gmail_credentials.json
│
├── logs/
│
├── token.json
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env
│
├── .env
└── README.md
```

> Do not commit `credentials/gmail_credentials.json`, `token.json`, or `.env` to a public repository.

---

# Backend Setup

## 1. Create and activate the virtual environment

From the project root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

---

## 2. Install backend dependencies

Install the project's Python dependencies.

If the project has a `requirements.txt`:

```powershell
pip install -r requirements.txt
```

If dependencies are being installed manually, make sure the environment contains the packages required by the FastAPI, Google, Pydantic, Supabase, dotenv, and testing components used by the project.

---

# Environment Variables

Create a `.env` file in the project root.

The exact values depend on your accounts and configuration.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Do not publish real API keys.

---

# Gmail Setup

The project uses Gmail OAuth.

Place the Google OAuth client credentials here:

```text
credentials/gmail_credentials.json
```

The application uses:

```text
token.json
```

to store the authorized Gmail OAuth token after authentication.

The distinction is:

```text
credentials/gmail_credentials.json
        ↓
Google OAuth client configuration

token.json
        ↓
Saved authorization for the Gmail account
```

If Gmail authentication needs to be performed again, the token can be regenerated through the application's authentication flow.

The Gmail scope used by the project is:

```text
https://www.googleapis.com/auth/gmail.send
```

---

# Running the Backend

From the project root:

```powershell
uvicorn app.main:app --reload --port 8000
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The API documentation is useful for development and debugging, but normal users should use the frontend instead.

---

# Frontend Setup

The frontend is a separate React + TypeScript + Vite application.

Go into the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create:

```text
frontend/.env
```

with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

This tells the frontend where the FastAPI backend is running.

For example:

```text
Frontend
http://localhost:5173

        ↓

Backend
http://127.0.0.1:8000
```

---

# Running the Frontend

From the `frontend` directory:

```powershell
npm run dev
```

Vite will normally show:

```text
Local: http://localhost:5173/
```

Open that address in your browser.

---

# Running the Complete System

You normally need two terminals.

## Terminal 1 — Backend

From:

```text
D:\Portfolio Website\AI Agent
```

run:

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

## Terminal 2 — Frontend

From:

```text
D:\Portfolio Website\AI Agentrontend
```

run:

```powershell
npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# Using the Application

## Add a lead

From the frontend:

1. Open **Add Lead**.
2. Enter the prospect's information.
3. Enter the prospect's message.
4. Click **Analyze Lead**.

The backend will run the pipeline.

---

## Lead pipeline

The backend performs:

```text
Create lead
    ↓
Analyze lead
    ↓
Score lead
    ↓
Research company
    ↓
Generate email
    ↓
Save result
```

The resulting lead appears in the frontend.

---

# Email Approval

Generated emails start in:

```text
Pending Approval
```

A user can:

### Approve

The email becomes:

```text
Approved
```

It can then be sent.

### Edit

The user can modify:
- Subject
- Body

before approving/sending.

### Reject

The email becomes:

```text
Rejected
```

and cannot be sent through the normal send workflow.

### Send

Only an approved email can be sent.

After successful Gmail delivery:

```text
Sent
```

The application records the send timestamp.

---

# Duplicate Send Protection

The workflow prevents an email that has already been sent from being sent again.

Conceptually:

```text
Pending → Approved → Sent
                     ↑
              cannot send again
```

This protects against accidental duplicate outreach.

---

# Error Handling

The system contains several layers of protection.

## Gemini retries

Lead analysis attempts the Gemini request up to three times.

```text
Attempt 1
   ↓ failure
Attempt 2
   ↓ failure
Attempt 3
   ↓ failure
Raise error
```

Logging records each attempt.

## Gmail failure

If Gmail fails to send an approved email:

```text
Approved
   ↓
Gmail error
   ↓
Email is NOT marked Sent
```

This prevents the database from claiming that an email was delivered when the Gmail operation actually failed.

---

# Testing

The project uses `pytest`.

Run:

```powershell
python -m pytest
```

The test suite covers the major pieces of the system, including:

- Lead scoring
- Email generation
- Gmail sending
- Company research
- Lead analysis
- Gemini retry behavior
- Full lead pipeline
- Email approval workflow
- Rejected email protection
- Duplicate-send protection
- Gmail failure handling

A successful run should look similar to:

```text
13 passed, 1 warning
```

The exact number may change as more tests are added.

---

# Test Philosophy

The tests intentionally separate external integrations from business logic where appropriate.

For example, Gmail tests can use mocked Gmail services instead of actually sending an email every time.

This makes the test suite:

- Faster
- Safer
- Repeatable
- Less dependent on external services

---

# Logging

Application logs are stored under the project's logging configuration, including the `logs/` directory where configured.

Useful events include:

```text
Lead created
Lead analyzed
Lead scored
Company research completed
Email draft generated
Email approved
Email rejected
Sending email
Email sent successfully
Gemini retry
External API failure
```

Logs are useful when debugging the pipeline without requiring the user to inspect every API request manually.

---

# Important Security Notes

Never commit these files to Git:

```text
.env
token.json
credentials/gmail_credentials.json
```

A recommended `.gitignore` includes:

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc

.env
token.json

credentials/gmail_credentials.json

logs/
frontend/node_modules/
frontend/dist/
```

API keys and OAuth credentials should remain private.

---

# Development Workflow

When developing the system:

```text
1. Start FastAPI
       ↓
2. Start Vite frontend
       ↓
3. Open browser
       ↓
4. Add fake/test lead
       ↓
5. Verify AI analysis
       ↓
6. Verify score
       ↓
7. Verify company research
       ↓
8. Verify email draft
       ↓
9. Approve/edit/reject
       ↓
10. Test Gmail sending
       ↓
11. Check Supabase state
       ↓
12. Check logs
       ↓
13. Run pytest
```

---

# Current Product Direction

The system is intended to evolve from a developer-oriented API into a user-friendly sales application.

The frontend is therefore the primary user interface.

A normal sales user should be able to perform the main workflow without knowing:

- FastAPI
- REST requests
- JSON payloads
- Gemini API calls
- Supabase queries
- Gmail API calls

Those are backend implementation details.

The intended user experience is:

```text
Sales user
    ↓
Web dashboard
    ↓
Add / review leads
    ↓
AI processing
    ↓
Human approval
    ↓
Email outreach
```

---

# Future Improvements

Potential next stages include:

- Automatic Gmail inbox lead fetching
- Email-to-lead conversion
- Gmail webhook/event processing
- Lead source tracking
- Authentication for multiple users
- Role-based access
- Pagination
- Advanced analytics
- Lead assignment
- CRM integrations
- Scheduled follow-ups
- Email reply tracking
- Conversation history
- Production deployment
- Background job processing
- Rate-limit handling
- Better observability and monitoring

---

# Tech Stack

## Backend

- Python
- FastAPI
- Pydantic
- Google Gemini
- Gmail API
- Supabase
- OAuth 2.0
- Pytest

## Frontend

- React
- TypeScript
- Vite
- React Router
- Lucide React

---

# Status

The project currently has a working end-to-end development workflow:

```text
Frontend
   ↓
FastAPI
   ↓
Lead creation
   ↓
AI analysis
   ↓
Scoring
   ↓
Company research
   ↓
Email generation
   ↓
Approval
   ↓
Gmail
   ↓
Sent
```

The main remaining product-level work is improving the user experience and adding automated lead intake so users do not need to manually enter every lead.
