import os
import base64
import json
import logging

from datetime import datetime, timezone
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

from app.tools.database import (
    get_gmail_connection,
    update_gmail_connection_tokens,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Gmail permissions
# ---------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


# ---------------------------------------------------------
# Legacy/local authentication files
# ---------------------------------------------------------

CREDENTIALS_FILE = (
    "credentials/gmail_credentials.json"
)

TOKEN_FILE = "token.json"


# ---------------------------------------------------------
# Web OAuth credentials
# ---------------------------------------------------------

WEB_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CLIENT_SECRET_FILE",
    "credentials/gmail_web_credentials.json",
)

GOOGLE_CLIENT_SECRET_JSON = os.getenv(
    "GOOGLE_CLIENT_SECRET_JSON"
)


# ---------------------------------------------------------
# Google OAuth configuration
# ---------------------------------------------------------


def _get_web_oauth_config() -> dict:
    """
    Return the Google Web OAuth client configuration.

    Production:
        GOOGLE_CLIENT_SECRET_JSON contains the complete
        Google OAuth JSON object.

    Local development:
        GOOGLE_CLIENT_SECRET_FILE points to the local
        credentials JSON file.
    """

    # -----------------------------------------------------
    # Production: environment variable
    # -----------------------------------------------------

    if GOOGLE_CLIENT_SECRET_JSON:
        try:
            oauth_config = json.loads(
                GOOGLE_CLIENT_SECRET_JSON
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "GOOGLE_CLIENT_SECRET_JSON contains invalid JSON"
            ) from exc

        if not isinstance(oauth_config, dict):
            raise ValueError(
                "GOOGLE_CLIENT_SECRET_JSON must contain a JSON object"
            )

        web_config = oauth_config.get("web")

        if not isinstance(web_config, dict):
            raise ValueError(
                "GOOGLE_CLIENT_SECRET_JSON must contain "
                "a 'web' configuration"
            )

        return oauth_config

    # -----------------------------------------------------
    # Local development: credentials file
    # -----------------------------------------------------

    if not os.path.exists(
        WEB_CREDENTIALS_FILE
    ):
        raise ValueError(
            "Google Web OAuth credentials file "
            "was not found at "
            f"{WEB_CREDENTIALS_FILE}"
        )

    try:
        with open(
            WEB_CREDENTIALS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            oauth_config = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Google Web OAuth credentials file contains invalid JSON"
        ) from exc

    if not isinstance(oauth_config, dict):
        raise ValueError(
            "Google Web OAuth credentials must contain "
            "a JSON object"
        )

    web_config = oauth_config.get("web")

    if not isinstance(web_config, dict):
        raise ValueError(
            "Invalid Google Web OAuth credentials: "
            "missing 'web' configuration"
        )

    return oauth_config


def _get_web_oauth_client_credentials() -> tuple[str, str]:
    """
    Return the Google OAuth client ID and client secret.
    """

    oauth_config = _get_web_oauth_config()

    web_config = oauth_config.get("web")

    client_id = web_config.get(
        "client_id"
    )

    client_secret = web_config.get(
        "client_secret"
    )

    if not client_id:
        raise ValueError(
            "Google Web OAuth credentials are missing "
            "client_id"
        )

    if not client_secret:
        raise ValueError(
            "Google Web OAuth credentials are missing "
            "client_secret"
        )

    return client_id, client_secret


# ---------------------------------------------------------
# Legacy Gmail service
#
# Keep this temporarily for existing tests/local tools.
# New authenticated application flows should use:
#
#     get_gmail_service_for_user(user_id)
# ---------------------------------------------------------


def get_gmail_service():
    creds = None

    # -----------------------------------------------------
    # Check for existing local token
    # -----------------------------------------------------

    if os.path.exists(
        TOKEN_FILE
    ):
        creds = (
            Credentials
            .from_authorized_user_file(
                TOKEN_FILE,
                SCOPES,
            )
        )

    # -----------------------------------------------------
    # Refresh or authenticate
    # -----------------------------------------------------

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            creds.refresh(
                Request()
            )

        else:

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES,
                )
            )

            creds = flow.run_local_server(
                port=0
            )

        # -------------------------------------------------
        # Save local token
        # -------------------------------------------------

        with open(
            TOKEN_FILE,
            "w",
        ) as token:

            token.write(
                creds.to_json()
            )

    # -----------------------------------------------------
    # Create Gmail service
    # -----------------------------------------------------

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


# ---------------------------------------------------------
# Per-user Gmail service
# ---------------------------------------------------------


def get_gmail_service_for_user(
    user_id: str,
):
    """
    Create a Gmail API service using the Gmail OAuth
    connection belonging to the authenticated application
    user.

    This is the service that should be used by the
    application's Gmail sync and email-sending flows.
    """

    # -----------------------------------------------------
    # Get saved Gmail connection
    # -----------------------------------------------------

    connection = get_gmail_connection(
        user_id=user_id
    )

    if not connection:
        raise ValueError(
            "Gmail is not connected for this user"
        )

    # -----------------------------------------------------
    # Get stored tokens
    # -----------------------------------------------------

    access_token = connection.get(
        "access_token"
    )

    refresh_token = connection.get(
        "refresh_token"
    )

    token_expiry = connection.get(
        "token_expiry"
    )

    if not access_token:
        raise ValueError(
            "Gmail connection has no access token"
        )

    # -----------------------------------------------------
    # Read OAuth client information
    #
    # Production:
    #   GOOGLE_CLIENT_SECRET_JSON
    #
    # Local:
    #   GOOGLE_CLIENT_SECRET_FILE
    # -----------------------------------------------------

    client_id, client_secret = (
        _get_web_oauth_client_credentials()
    )

    # -----------------------------------------------------
    # Convert stored expiry to datetime
    # -----------------------------------------------------

    expiry = None

    if token_expiry:

        try:

            expiry = datetime.fromisoformat(
                token_expiry
            )

            # Google authentication expects a timezone-naive
            # UTC datetime for credential expiry.
            if expiry.tzinfo is not None:
                expiry = (
                    expiry
                    .astimezone(timezone.utc)
                    .replace(
                        tzinfo=None
                    )
                )

        except ValueError:

            expiry = None

    # -----------------------------------------------------
    # Create Google credentials
    # -----------------------------------------------------

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=(
            "https://oauth2.googleapis.com/token"
        ),
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
        expiry=expiry,
    )

    # -----------------------------------------------------
    # Refresh expired access token
    # -----------------------------------------------------

    if (
        credentials.expired
        and credentials.refresh_token
    ):

        try:

            credentials.refresh(
                Request()
            )

        except RefreshError as e:

            logger.exception(
                "Failed to refresh Gmail credentials "
                f"for user {user_id}"
            )

            raise RuntimeError(
                "Gmail authorization has expired or "
                "has been revoked. Please reconnect "
                "your Gmail account."
            ) from e

        # -------------------------------------------------
        # Save refreshed credentials
        # -------------------------------------------------

        new_expiry = None

        if credentials.expiry:

            new_expiry = (
                credentials
                .expiry
                .astimezone()
                .isoformat()
            )

        update_gmail_connection_tokens(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=(
                credentials.refresh_token
            ),
            token_expiry=new_expiry,
        )

    # -----------------------------------------------------
    # Build Gmail API service
    # -----------------------------------------------------

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )


# ---------------------------------------------------------
# Send email for a specific application user
# ---------------------------------------------------------


def send_email(
    recipient: str,
    subject: str,
    body: str,
    user_id: str | None = None,
):
    """
    Send an email using Gmail API.

    If user_id is provided, use the Gmail connection
    belonging to that authenticated application user.

    If user_id is not provided, fall back to the legacy
    local OAuth flow.
    """

    # -----------------------------------------------------
    # Get Gmail service
    # -----------------------------------------------------

    if user_id:

        service = get_gmail_service_for_user(
            user_id=user_id
        )

    else:

        service = get_gmail_service()

    # -----------------------------------------------------
    # Create email
    # -----------------------------------------------------

    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    # -----------------------------------------------------
    # Encode message
    # -----------------------------------------------------

    encoded_message = (
        base64.urlsafe_b64encode(
            message.as_bytes()
        )
        .decode()
    )

    gmail_message = {
        "raw": encoded_message
    }

    # -----------------------------------------------------
    # Send
    # -----------------------------------------------------

    sent_message = (
        service
        .users()
        .messages()
        .send(
            userId="me",
            body=gmail_message,
        )
        .execute()
    )

    return sent_message


# ---------------------------------------------------------
# Mark Gmail message as read
# ---------------------------------------------------------


def mark_message_as_read(
    service,
    message_id: str,
):
    """
    Remove the UNREAD label from a Gmail message.
    """

    print(
        f"MARKING GMAIL MESSAGE AS READ: "
        f"{message_id}"
    )

    result = (
        service
        .users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={
                "removeLabelIds": [
                    "UNREAD"
                ]
            },
        )
        .execute()
    )

    print(
        f"GMAIL MODIFY RESULT: {result}"
    )

    return result
