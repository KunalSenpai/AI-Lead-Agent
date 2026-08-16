import logging

from app.tools.gmail import (
    get_gmail_service,
    mark_message_as_read,
)
from app.tools.gmail_parser import parse_gmail_message
from app.services.gmail_lead_detector import is_potential_lead
from app.agents.gmail_lead_agent import extract_lead_from_email
from app.tools.database import (
    get_lead_by_source,
    save_lead,
)


logger = logging.getLogger(__name__)


def fetch_and_create_gmail_leads(
    max_results: int = 20,
    service=None,
    user_id: str | None = None,
):
    """
    Fetch unread Gmail messages, identify potential leads,
    extract lead information, and create new Supabase leads.

    The created lead is associated with the authenticated
    application user through user_id.

    Does NOT run the downstream AI lead pipeline yet.
    """

    # ---------------------------------------------------------
    # Get Gmail service
    # ---------------------------------------------------------

    if service is None:
        service = get_gmail_service()

    # ---------------------------------------------------------
    # Fetch unread Gmail messages
    # ---------------------------------------------------------

    response = (
        service
        .users()
        .messages()
        .list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        )
        .execute()
    )

    messages = response.get("messages", [])

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    results = {
        "messages_checked": 0,
        "leads_created": 0,
        "duplicates_skipped": 0,
        "non_leads_skipped": 0,
        "created_leads": [],
    }

    # ---------------------------------------------------------
    # Process messages
    # ---------------------------------------------------------

    for message in messages:

        results["messages_checked"] += 1

        message_id = message["id"]

        # -----------------------------------------------------
        # Get full Gmail message
        # -----------------------------------------------------

        full_message = (
            service
            .users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        # -----------------------------------------------------
        # Parse Gmail message
        # -----------------------------------------------------

        parsed = parse_gmail_message(
            full_message
        )

        # -----------------------------------------------------
        # Ignore non-leads
        # -----------------------------------------------------

        if not is_potential_lead(parsed):

            results["non_leads_skipped"] += 1

            continue

        # -----------------------------------------------------
        # Check for existing Gmail lead
        # -----------------------------------------------------

        existing_lead = get_lead_by_source(
            source_type="gmail",
            source_id=message_id,
        )

        if existing_lead:

            results["duplicates_skipped"] += 1

            logger.info(
                f"Duplicate Gmail message "
                f"{message_id} found. "
                f"Existing lead status: "
                f"{existing_lead.get('email_status')}"
            )

            # -------------------------------------------------
            # Only mark an existing successfully processed
            # lead as read.
            #
            # Failed leads remain unread so they can be
            # retried on a future sync.
            # -------------------------------------------------

            if existing_lead.get("email_status") != "failed":

                try:

                    logger.info(
                        f"Attempting to mark Gmail message "
                        f"{message_id} as READ"
                    )

                    mark_message_as_read(
                        service=service,
                        message_id=message_id,
                    )

                    logger.info(
                        f"Gmail message "
                        f"{message_id} marked as READ"
                    )

                except Exception:

                    logger.exception(
                        f"Failed to mark Gmail message "
                        f"{message_id} as read"
                    )

            else:

                logger.info(
                    f"Gmail message {message_id} belongs "
                    f"to a failed lead. Leaving message unread "
                    f"for retry."
                )

            continue

        # -----------------------------------------------------
        # Extract structured lead
        # -----------------------------------------------------

        extracted = extract_lead_from_email(
            parsed
        )

        # -----------------------------------------------------
        # Create Supabase lead
        # -----------------------------------------------------

        saved_lead = save_lead(
            name=extracted.name,
            email=extracted.email,
            company=extracted.company or "Unknown",
            website=extracted.website,
            job_title=extracted.job_title,
            message=extracted.message,
            source_type="gmail",
            source_id=message_id,
            user_id=user_id,
        )

        # -----------------------------------------------------
        # Update results
        # -----------------------------------------------------

        results["leads_created"] += 1

        results["created_leads"].append(
            saved_lead
        )

        logger.info(
            f"Created Gmail lead "
            f"{saved_lead.get('id')} "
            f"from message {message_id} "
            f"for user {user_id}"
        )

    return results