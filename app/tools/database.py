import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL or SUPABASE_KEY is missing from .env"
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def get_supabase_admin() -> Client:
    """
    Create a privileged Supabase client for trusted
    server-side operations that need to bypass RLS.
    """

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY is missing"
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
    )


# =========================================================
# LEADS
# =========================================================


def save_lead(
    name: str,
    email: str,
    company: str,
    website: str | None,
    job_title: str | None,
    message: str,
    source_type: str | None = None,
    source_id: str | None = None,
    user_id: str | None = None,
):
    if not user_id:
        raise ValueError(
            "user_id is required when saving a lead"
        )

    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("leads")
        .insert({
            "name": name,
            "email": email,
            "company": company,
            "website": website,
            "job_title": job_title,
            "message": message,
            "source_type": source_type,
            "source_id": source_id,
            "user_id": user_id,
        })
        .execute()
    )

    if not response.data:
        raise Exception(
            "Lead insert returned no data"
        )

    return response.data[0]


def get_lead(
    lead_id: int,
    user_id: str,
):
    if not user_id:
        raise ValueError(
            "user_id is required when fetching a lead"
        )

    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("leads")
        .select("*")
        .eq("id", lead_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise Exception(
            f"Lead with id {lead_id} was not found"
        )

    return response.data[0]

def list_leads(
    user_id: str,
    status: str | None = None,
):
    if not user_id:
        raise ValueError(
            "user_id is required when listing leads"
        )

    supabase_admin = get_supabase_admin()

    query = (
        supabase_admin
        .table("leads")
        .select("*")
        .eq("user_id", user_id)
        .order(
            "created_at",
            desc=True,
        )
    )

    if status:
        query = query.eq(
            "email_status",
            status,
        )

    response = query.execute()

    return response.data

def get_lead_by_source(
    source_type: str,
    source_id: str,
    user_id: str,
):
    response = (
        supabase
        .table("leads")
        .select("*")
        .eq("source_type", source_type)
        .eq("source_id", source_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# =========================================================
# AI ANALYSIS / SCORE / RESEARCH / EMAIL
# =========================================================


def save_analysis_score_research_and_email(
    lead_id,
    user_id: str,
    industry: str,
    company_size: int | None,
    lead_volume: int | None,
    problem: str,
    urgency: str,
    score: int,
    category: str,
    score_reasons: list[str],
    research_data: dict,
    email_subject: str,
    email_body: str,
):
    if not user_id:
        raise ValueError(
            "user_id is required when saving pipeline results"
        )

    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("leads")
        .update({
            # AI analysis
            "industry": industry,
            "company_size": company_size,
            "lead_volume": lead_volume,
            "problem": problem,
            "urgency": urgency,

            # Lead score
            "score": score,
            "category": category,
            "score_reasons": score_reasons,

            # Company research
            "research_summary": research_data["summary"],
            "research_data": research_data,
            "research_sources": research_data["source_urls"],

            # Email draft
            "email_subject": email_subject,
            "email_body": email_body,
            "email_status": "pending_approval",
        })
        .eq(
            "id",
            lead_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            "Failed to save analysis, score, research and email"
        )

    return response.data[0]


# =========================================================
# EMAIL STATUS
# =========================================================


def update_email_status(
    lead_id: int,
    status: str,
    user_id: str,
):
    allowed_statuses = {
        "pending_approval",
        "approved",
        "rejected",
        "sent",
        "failed",
    }

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid email status: {status}"
        )

    response = (
        supabase
        .table("leads")
        .update({
            "email_status": status,
        })
        .eq(
            "id",
            lead_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            f"Lead with id {lead_id} was not found"
        )

    return response.data[0]


def update_email_draft(
    lead_id: int,
    subject: str,
    body: str,
    user_id: str,
):
    response = (
        supabase
        .table("leads")
        .update({
            "email_subject": subject,
            "email_body": body,
            "email_status": "pending_approval",
        })
        .eq(
            "id",
            lead_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            f"Lead with id {lead_id} was not found"
        )

    return response.data[0]


def mark_email_as_sent(
    lead_id: int,
    user_id: str,
    gmail_message_id: str,
):
    """
    Mark an approved lead as sent and persist the
    outgoing Gmail message ID.

    The user_id filter ensures that one application
    user cannot modify another user's lead.
    """

    sent_at = datetime.now(
        timezone.utc
    ).isoformat()

    response = (
        supabase
        .table("leads")
        .update({
            "email_status": "sent",
            "sent_at": sent_at,
            "gmail_message_id": gmail_message_id,
        })
        .eq(
            "id",
            lead_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            f"Lead with id {lead_id} was not found"
        )

    return response.data[0]


# =========================================================
# GMAIL CONNECTION
# =========================================================


def save_gmail_connection(
    user_id: str,
    gmail_email: str,
    access_token: str,
    refresh_token: str | None,
    token_expiry: str | None,
):
    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("gmail_connections")
        .upsert(
            {
                "user_id": user_id,
                "gmail_email": gmail_email,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expiry": token_expiry,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            on_conflict="user_id",
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            "Failed to save Gmail connection"
        )

    return response.data[0]


def get_gmail_connection(
    user_id: str,
):
    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("gmail_connections")
        .select("*")
        .eq(
            "user_id",
            user_id,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def delete_gmail_connection(
    user_id: str,
):
    """
    Delete the Gmail connection belonging to
    the authenticated application user.
    """

    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("gmail_connections")
        .delete()
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    return response.data


def update_gmail_connection_tokens(
    user_id: str,
    access_token: str,
    refresh_token: str | None,
    token_expiry: str | None,
):
    update_data = {
        "access_token": access_token,
        "token_expiry": token_expiry,
    }

    # Google may not return a new refresh token
    # during every refresh. Preserve the existing
    # refresh token when Google does not provide
    # a replacement.
    if refresh_token:
        update_data["refresh_token"] = refresh_token

    supabase_admin = get_supabase_admin()

    response = (
        supabase_admin
        .table("gmail_connections")
        .update(update_data)
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    if not response.data:
        raise Exception(
            "Gmail connection was not found "
            f"for user {user_id}"
        )

    return response.data[0]