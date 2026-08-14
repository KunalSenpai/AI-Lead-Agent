import os
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ---------------------------------------------------------
# Gmail permissions
# ---------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


# ---------------------------------------------------------
# File locations
# ---------------------------------------------------------

CREDENTIALS_FILE = "credentials/gmail_credentials.json"
TOKEN_FILE = "token.json"


# ---------------------------------------------------------
# Authenticate with Google
# ---------------------------------------------------------

def get_gmail_service():

    creds = None

    # -----------------------------------------------------
    # Check if we already have a saved login
    # -----------------------------------------------------

    if os.path.exists(TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # -----------------------------------------------------
    # If credentials don't exist or are invalid
    # -----------------------------------------------------

    if not creds or not creds.valid:

        # Refresh expired credentials if possible

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        # Save credentials for future use

        with open(TOKEN_FILE, "w") as token:

            token.write(
                creds.to_json()
            )

    # -----------------------------------------------------
    # Create Gmail API service
    # -----------------------------------------------------

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service

def send_email(
    recipient: str,
    subject: str,
    body: str
):
    """
    Send an email using Gmail API.
    """

    # -----------------------------------------
    # Step 1: Get authenticated Gmail service
    # -----------------------------------------

    service = get_gmail_service()

    # -----------------------------------------
    # Step 2: Create the email
    # -----------------------------------------

    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    # -----------------------------------------
    # Step 3: Convert email to Gmail format
    # -----------------------------------------

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    # -----------------------------------------
    # Step 4: Prepare Gmail API request
    # -----------------------------------------

    gmail_message = {
        "raw": encoded_message
    }

    # -----------------------------------------
    # Step 5: Send email
    # -----------------------------------------

    sent_message = (
        service
        .users()
        .messages()
        .send(
            userId="me",
            body=gmail_message
        )
        .execute()
    )

    return sent_message