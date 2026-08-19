import logging

from app.tools.gmail import (
    get_gmail_service,
    get_gmail_service_for_user,
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

    Gmail pagination is handled automatically until there are
    no more pages.

    A failure processing one message does not stop the rest
    of the sync.
    """

    # ---------------------------------------------------------
    # Gmail service
    # ---------------------------------------------------------

    if service is None:

        if user_id:

            service = get_gmail_service_for_user(
                user_id=user_id
            )

        else:

            service = get_gmail_service()

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    results = {
        "messages_checked": 0,
        "leads_created": 0,
        "duplicates_skipped": 0,
        "non_leads_skipped": 0,
        "created_leads": [],
        "failed_messages": [],
    }

    # ---------------------------------------------------------
    # Gmail pagination
    # ---------------------------------------------------------

    page_token = None

    while True:

        logger.info(
            "GMAIL SYNC QUERY | "
            f"user_id={user_id} | "
            f"max_results={max_results} | "
            f"page_token={page_token}"
        )

        list_kwargs = {
            "userId": "me",
            "q": (
                "in:inbox "
                "is:unread "
                "newer_than:90d "
                "-category:promotions"
            ),
            "maxResults": max_results,
        }

        if page_token:
            list_kwargs["pageToken"] = page_token

        response = (
            service
            .users()
            .messages()
            .list(**list_kwargs)
            .execute()
        )

        messages = response.get(
            "messages",
            []
        )

        logger.info(
            "GMAIL SYNC RESULT | "
            f"messages_returned={len(messages)} | "
            f"message_ids="
            f"{[m.get('id') for m in messages]} | "
            f"page_token={page_token}"
        )

        # -----------------------------------------------------
        # Process current page
        # -----------------------------------------------------

        for message in messages:

            results["messages_checked"] += 1

            message_id = message.get(
                "id"
            )

            if not message_id:

                logger.warning(
                    "Gmail message did not contain "
                    "an ID. Skipping."
                )

                continue

            try:

                # -------------------------------------------------
                # Get full Gmail message
                # -------------------------------------------------

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

                logger.info(
                    "GMAIL MESSAGE FETCHED | "
                    f"message_id={message_id}"
                )

                # -------------------------------------------------
                # Parse Gmail message
                # -------------------------------------------------

                parsed = parse_gmail_message(
                    full_message
                )

                logger.info(
                    "GMAIL MESSAGE PARSED | "
                    f"message_id={message_id} | "
                    f"sender={parsed.get('email')} | "
                    f"subject={parsed.get('subject')} | "
                    f"body="
                    f"{parsed.get('body', '')[:500]}"
                )

                # -------------------------------------------------
                # Ignore non-leads
                # -------------------------------------------------

                potential_lead = is_potential_lead(
                    parsed
                )

                logger.info(
                    "GMAIL LEAD DETECTOR | "
                    f"message_id={message_id} | "
                    f"result={potential_lead}"
                )

                if not potential_lead:

                    results[
                        "non_leads_skipped"
                    ] += 1

                    continue

                # -------------------------------------------------
                # Check for existing Gmail lead
                # -------------------------------------------------

                existing_lead = get_lead_by_source(
                    source_type="gmail",
                    source_id=message_id,
                    user_id=user_id,
                )

                if existing_lead:

                    results[
                        "duplicates_skipped"
                    ] += 1

                    logger.info(
                        f"Duplicate Gmail message "
                        f"{message_id} found. "
                        f"Existing lead status: "
                        f"{existing_lead.get('email_status')}"
                    )

                    # ---------------------------------------------
                    # Only mark an existing successfully processed
                    # lead as read.
                    #
                    # Failed leads remain unread so they can be
                    # retried on a future sync.
                    # ---------------------------------------------

                    if (
                        existing_lead.get(
                            "email_status"
                        )
                        != "failed"
                    ):

                        try:

                            logger.info(
                                f"Attempting to mark Gmail "
                                f"message {message_id} as READ"
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
                                f"Failed to mark Gmail "
                                f"message {message_id} as read"
                            )

                    else:

                        logger.info(
                            f"Gmail message "
                            f"{message_id} belongs to a "
                            f"failed lead. Leaving message "
                            f"unread for retry."
                        )

                    continue

                # -------------------------------------------------
                # Extract structured lead
                # -------------------------------------------------

                extracted = (
                    extract_lead_from_email(
                        parsed
                    )
                )

                # -------------------------------------------------
                # Create Supabase lead
                # -------------------------------------------------

                saved_lead = save_lead(
                    name=extracted.name,
                    email=extracted.email,
                    company=(
                        extracted.company
                        or "Unknown"
                    ),
                    website=extracted.website,
                    job_title=extracted.job_title,
                    message=extracted.message,
                    source_type="gmail",
                    source_id=message_id,
                    user_id=user_id,
                )

                # -------------------------------------------------
                # Update results
                # -------------------------------------------------

                results[
                    "leads_created"
                ] += 1

                results[
                    "created_leads"
                ].append(
                    saved_lead
                )

                logger.info(
                    f"Created Gmail lead "
                    f"{saved_lead.get('id')} "
                    f"from message {message_id} "
                    f"for user {user_id}"
                )

            except Exception as e:

                # -------------------------------------------------
                # Isolate failures to this individual message.
                #
                # The rest of the Gmail sync should continue.
                # -------------------------------------------------

                logger.exception(
                    f"Failed to process Gmail message "
                    f"{message_id} for user {user_id}"
                )

                results[
                    "failed_messages"
                ].append(
                    {
                        "message_id": message_id,
                        "error": str(e),
                    }
                )

                continue

        # ---------------------------------------------------------
        # Check for another Gmail page
        # ---------------------------------------------------------

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return results