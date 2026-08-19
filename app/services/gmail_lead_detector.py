import logging
import os
import re

from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)


GMAIL_USER_EMAIL = (
    os.getenv("GMAIL_USER_EMAIL") or ""
).lower().strip()


# =========================================================
# Sender/domain exclusions
# =========================================================

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


# =========================================================
# Strong non-lead / transactional signals
# =========================================================

NON_LEAD_KEYWORDS = {
    # Account verification
    "verify your email",
    "verify your account",
    "email verification",
    "account verification",
    "confirm your email",
    "confirm your account",
    "verification code",
    "verification link",
    "verify email address",

    # Authentication / security
    "one-time password",
    "one time password",
    "otp",
    "security code",
    "security alert",
    "password reset",
    "reset your password",
    "sign-in attempt",
    "login attempt",
    "login verification",
    "authentication code",
    "authentication",

    # Generic account notifications
    "account activated",
    "account created",
    "welcome to",
    "confirm subscription",
    "subscription confirmed",

    # Transactional
    "order confirmation",
    "order confirmed",
    "payment confirmation",
    "payment received",
    "invoice",
    "receipt",
    "transaction",
    "shipping confirmation",
    "delivery confirmation",
    "your package",
    "your order",

    # Generic automated notifications
    "automated message",
    "automated notification",
    "do not reply",
    "this is an automated",
}


# =========================================================
# Marketing signals
# =========================================================

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


# =========================================================
# Strong lead intent phrases
# =========================================================

STRONG_LEAD_PHRASES = {
    "i am interested",
    "i'm interested",
    "we are interested",
    "we're interested",
    "interested in your",
    "interested in your services",
    "interested in your service",
    "interested in your product",
    "interested in working with",
    "would like a demo",
    "would like to schedule",
    "would like to discuss",
    "request a demo",
    "request pricing",
    "request a quote",
    "request a proposal",
    "looking for a solution",
    "looking for your services",
    "looking for help",
    "need help with",
    "need a solution",
    "we need",
    "we are looking for",
    "we're looking for",
    "can you help us",
    "could you help us",
    "please contact me",
    "please get in touch",
    "schedule a call",
    "book a call",
    "set up a call",
    "want to discuss",
    "would like to learn more",
}


# =========================================================
# Existing lead keywords
# =========================================================

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


# =========================================================
# Business-context keywords
# =========================================================

BUSINESS_CONTEXT_KEYWORDS = {
    "company",
    "business",
    "team",
    "employees",
    "customers",
    "clients",
    "sales team",
    "sales process",
    "leads",
    "lead generation",
    "workflow",
    "automation",
    "integration",
    "implementation",
    "requirements",
    "project",
    "budget",
    "monthly",
    "annually",
}


def _contains_phrase(
    content: str,
    phrases: set[str],
) -> bool:

    for phrase in phrases:

        if phrase in content:
            return True

    return False


def _count_keyword_matches(
    content: str,
    keywords: set[str],
) -> int:

    matches = 0

    for keyword in keywords:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            content,
        ):
            matches += 1

    return matches


def is_potential_lead(
    email_data: dict,
) -> bool:

    sender_email = (
        email_data.get("email") or ""
    ).lower().strip()

    subject = (
        email_data.get("subject") or ""
    ).lower().strip()

    body = (
        email_data.get("body") or ""
    ).lower().strip()

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

        domain = sender_email.split(
            "@",
            1,
        )[1]

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

    logger.debug(
        "GMAIL DETECTOR DEBUG | "
        f"sender={sender_email} | "
        f"subject={subject} | "
        f"strong_phrase_matches="
        f"{[
            phrase
            for phrase in STRONG_LEAD_PHRASES
            if phrase in content
        ]} | "
        f"non_lead_matches="
        f"{[
            phrase
            for phrase in NON_LEAD_KEYWORDS
            if phrase in content
        ]}"
    )

    # -----------------------------------------------------
    # Strong non-lead signals
    #
    # These should take priority over weak positive
    # keywords.
    # -----------------------------------------------------

    if _contains_phrase(
        content,
        NON_LEAD_KEYWORDS,
    ):
        return False

    # -----------------------------------------------------
    # Marketing signals
    # -----------------------------------------------------

    marketing_matches = _count_keyword_matches(
        content,
        MARKETING_KEYWORDS,
    )

    if marketing_matches >= 1:
        return False

    # -----------------------------------------------------
    # Strong direct lead intent
    #
    # A direct commercial request is enough to qualify.
    # -----------------------------------------------------

    if _contains_phrase(
        content,
        STRONG_LEAD_PHRASES,
    ):
        return True

    # -----------------------------------------------------
    # Weak lead signals
    #
    # A single generic word such as "services" should NOT
    # automatically turn an email into a lead.
    # -----------------------------------------------------

    lead_matches = _count_keyword_matches(
        content,
        LEAD_KEYWORDS,
    )

    business_matches = _count_keyword_matches(
        content,
        BUSINESS_CONTEXT_KEYWORDS,
    )

    # -----------------------------------------------------
    # Require stronger evidence when using generic
    # keywords.
    #
    # Examples:
    #
    # "pricing" + "company"      -> lead
    # "demo" + "business"       -> lead
    # "services" alone           -> not enough
    # "solution" alone           -> not enough
    # -----------------------------------------------------

    if lead_matches >= 2:
        return True

    if (
        lead_matches >= 1
        and business_matches >= 1
    ):
        return True

    return False