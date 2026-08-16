import base64
from email.utils import parseaddr


def get_header(headers: list[dict], name: str) -> str | None:
    """
    Get a Gmail header value by name.
    """

    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")

    return None


def decode_body(data: str | None) -> str:
    """
    Decode a Gmail base64url encoded body.
    """

    if not data:
        return ""

    try:
        decoded = base64.urlsafe_b64decode(
            data.encode("UTF-8")
        )

        return decoded.decode(
            "UTF-8",
            errors="replace"
        )

    except Exception:
        return ""


def extract_text_from_payload(payload: dict) -> str:
    """
    Extract text from a Gmail MIME payload.

    Prefer text/plain when available.
    Recursively inspect nested MIME parts.
    """

    mime_type = payload.get("mimeType")

    body = payload.get("body", {})
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return decode_body(data)

    parts = payload.get("parts", [])

    plain_text = []

    for part in parts:

        text = extract_text_from_payload(part)

        if text:
            plain_text.append(text)

    return "\n".join(plain_text)


def parse_gmail_message(message: dict) -> dict:
    """
    Convert a raw Gmail API message into a clean structure.
    """

    payload = message.get("payload", {})

    headers = payload.get("headers", [])

    sender = get_header(headers, "From")
    subject = get_header(headers, "Subject")

    name, email = parseaddr(sender or "")

    body = extract_text_from_payload(payload)

    return {
        "message_id": message.get("id"),
        "name": name or None,
        "email": email or None,
        "subject": subject or "",
        "body": body.strip(),
    }