import os
import re

from dotenv import load_dotenv


load_dotenv()


GMAIL_USER_EMAIL = (
    os.getenv("GMAIL_USER_EMAIL") or ""
).lower().strip()


IGNORED_SENDER_DOMAINS = {
    "googlemail.com",
    "google.com",
}


IGNORED_EMAIL_PREFIXES = {
    "mailer-daemon",
    "no-reply",
    "noreply",
    "notifications",
}


AUTOMATED_SENDER_PREFIXES = {
    "support",
    "marketing",
    "newsletter",
    "news",
    "updates",
    "offers",
    "promo",
    "notifications",
    "mailer",
    "no-reply",
    "noreply",
}


LEAD_KEYWORDS = {
    "interested",
    "pricing",
    "price",
    "demo",
    "quote",
    "quotation",
    "proposal",
    "consultation",
    "consult",
    "sales",
    "services",
    "solution",
    "enquiry",
    "inquiry",
    "qualification",
}


MARKETING_KEYWORDS = {
    "unsubscribe",
    "newsletter",
    "promotion",
    "promo",
    "limited time",
    "last chance",
    "special offer",
    "exclusive offer",
    "discount",
    "sale ends",
    "shop now",
    "buy now",
    "upgrade today",
    "join the challenge",
    "starts tomorrow",
    "free trial",
    "order now",
}


def is_potential_lead(email_data: dict) -> bool:

    sender_email = (
        email_data.get("email") or ""
    ).lower().strip()

    subject = (
        email_data.get("subject") or ""
    ).lower()

    body = (
        email_data.get("body") or ""
    ).lower()

    if not sender_email:
        return False

    # -----------------------------------------------------
    # Ignore our own emails
    # -----------------------------------------------------

    if (
        GMAIL_USER_EMAIL
        and sender_email == GMAIL_USER_EMAIL
    ):
        return False

    # -----------------------------------------------------
    # Sender information
    # -----------------------------------------------------

    local_part = sender_email.split("@")[0]

    if local_part in IGNORED_EMAIL_PREFIXES:
        return False

    if "@" in sender_email:

        domain = sender_email.split("@", 1)[1]

        if domain in IGNORED_SENDER_DOMAINS:
            return False

    # -----------------------------------------------------
    # Ignore obvious automated/marketing senders
    # -----------------------------------------------------

    if local_part in AUTOMATED_SENDER_PREFIXES:
        return False

    # -----------------------------------------------------
    # Combine content
    # -----------------------------------------------------

    content = f"{subject}\n{body}"

    # -----------------------------------------------------
    # Strong marketing signals
    # -----------------------------------------------------

    marketing_matches = 0

    for keyword in MARKETING_KEYWORDS:

        if keyword in content:
            marketing_matches += 1

    # Multiple marketing signals strongly suggest
    # this is a newsletter or promotional email.
    if marketing_matches >= 1:
        return False

    # -----------------------------------------------------
    # Lead signals
    # -----------------------------------------------------

    lead_matches = 0

    for keyword in LEAD_KEYWORDS:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            content,
        ):
            lead_matches += 1

    return lead_matches >= 1