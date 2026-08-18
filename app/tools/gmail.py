import os
import base64

from datetime import datetime, timezone
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.tools.database import (
    get_gmail_connection,
    update_gmail_connection_tokens,
)


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
#
# This is the credential file used when the user
# connected Gmail through /gmail/connect.
# ---------------------------------------------------------

WEB_CREDENTIALS_FILE = (
    "credentials/gmail_web_credentials.json"
)


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

    if os.path.exists(TOKEN_FILE):

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
    # from the Web OAuth credentials file
    # -----------------------------------------------------

    if not os.path.exists(
        WEB_CREDENTIALS_FILE
    ):
        raise ValueError(
            "Google Web OAuth credentials file "
            "was not found at "
            f"{WEB_CREDENTIALS_FILE}"
        )

    import json

    with open(
        WEB_CREDENTIALS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        oauth_config = json.load(file)

    # Google Web OAuth credentials normally have
    # the client configuration under "web".
    web_config = oauth_config.get(
        "web"
    )

    if not web_config:
        raise ValueError(
            "Invalid Google Web OAuth credentials file: "
            "missing 'web' configuration"
        )

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
                expiry = expiry.astimezone(
                    timezone.utc
                ).replace(
                    tzinfo=None
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

        credentials.refresh(
            Request()
        )

        # -------------------------------------------------
        # Save refreshed credentials
        # -------------------------------------------------

        new_expiry = None

        if credentials.expiry:

            new_expiry = (
                credentials.expiry
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