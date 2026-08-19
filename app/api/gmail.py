import os
from urllib.parse import urlencode

from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.auth import get_current_user
from app.tools.database import (
    save_gmail_connection,
    get_gmail_connection,
    delete_gmail_connection,
)
from app.tools.gmail_oauth import (
    create_oauth_state,
    verify_oauth_state,
)
# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Router
# ---------------------------------------------------------

router = APIRouter(
    prefix="/gmail",
    tags=["gmail"],
)


# ---------------------------------------------------------
# Google OAuth configuration
# ---------------------------------------------------------

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID"
)

GOOGLE_CLIENT_SECRET_FILE = (
    "credentials/gmail_web_credentials.json"
)

GOOGLE_REDIRECT_URI = (
    "http://127.0.0.1:8000/gmail/oauth/callback"
)
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
).rstrip("/")


# ---------------------------------------------------------
# Gmail permissions
# ---------------------------------------------------------

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


# ---------------------------------------------------------
# Start Gmail OAuth
# ---------------------------------------------------------

@router.get("/connect")
def connect_gmail(
    user=Depends(get_current_user),
):
    """
    Start the Google OAuth flow for the
    authenticated application user.
    """

    # -----------------------------------------------------
    # Make sure Google client ID exists
    # -----------------------------------------------------

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail=(
                "GOOGLE_CLIENT_ID is not configured "
                "in the backend .env file"
            ),
        )

    # -----------------------------------------------------
    # Make sure Web OAuth credentials exist
    # -----------------------------------------------------

    if not os.path.exists(
        GOOGLE_CLIENT_SECRET_FILE
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Google Web OAuth credentials file "
                "was not found at "
                f"{GOOGLE_CLIENT_SECRET_FILE}"
            ),
        )

    # -----------------------------------------------------
    # Build Google authorization URL
    # -----------------------------------------------------
    state = create_oauth_state(
                user_id=str(user.id),
            )
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }


    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    # -----------------------------------------------------
    # Return URL to frontend
    # -----------------------------------------------------

    return {
        "success": True,
        "authorization_url": authorization_url,
    }


# ---------------------------------------------------------
# Google OAuth callback
# ---------------------------------------------------------

@router.get("/oauth/callback")
def gmail_oauth_callback(
    code: str,
    state: str,
):
    """
    Receive the Google OAuth authorization code,
    exchange it for Gmail credentials, retrieve
    the Gmail account email, and save the connection
    for the application user.
    """

    try:

        # -------------------------------------------------
        # Validate OAuth credentials file
        # -------------------------------------------------

        if not os.path.exists(
            GOOGLE_CLIENT_SECRET_FILE
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Google Web OAuth credentials file "
                    "was not found at "
                    f"{GOOGLE_CLIENT_SECRET_FILE}"
                ),
            )

        # -------------------------------------------------
        # Validate OAuth state
        # -------------------------------------------------

        try:

            user_id = verify_oauth_state(
                state
            )

        except ValueError as e:

            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        # -------------------------------------------------
        # Create OAuth flow
        # -------------------------------------------------

        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRET_FILE,
            scopes=GMAIL_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )

        # -------------------------------------------------
        # Exchange authorization code for credentials
        # -------------------------------------------------

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        if not credentials.token:
            raise Exception(
                "Google OAuth did not return an access token"
            )

        # -------------------------------------------------
        # Create Gmail service
        # -------------------------------------------------

        gmail_service = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

        # -------------------------------------------------
        # Get connected Gmail account
        # -------------------------------------------------

        profile = (
            gmail_service
            .users()
            .getProfile(
                userId="me"
            )
            .execute()
        )

        gmail_email = profile.get(
            "emailAddress"
        )

        if not gmail_email:
            raise Exception(
                "Unable to determine Gmail account email"
            )

        # -------------------------------------------------
        # Get token expiry
        # -------------------------------------------------

        token_expiry = None

        if credentials.expiry:
            token_expiry = (
                credentials.expiry
                .astimezone()
                .isoformat()
            )

        # -------------------------------------------------
        # Save Gmail connection
        # -------------------------------------------------

        save_gmail_connection(
            user_id=user_id,
            gmail_email=gmail_email,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
        )

        # -------------------------------------------------
        # OAuth completed successfully
        # -------------------------------------------------

        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard?gmail=connected"
)
    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Gmail OAuth failed: {str(e)}"
            ),
        )

@router.get("/status")
def gmail_status(
    user=Depends(get_current_user),
):
    """
    Return Gmail connection status for the
    authenticated application user.
    """

    try:

        connection = get_gmail_connection(
            user_id=str(user.id)
        )

        if not connection:

            return {
                "connected": False,
                "gmail_email": None,
            }

        return {
            "connected": True,
            "gmail_email": connection.get(
                "gmail_email"
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to check Gmail connection: "
                f"{str(e)}"
            ),
        )

@router.delete("/disconnect")
def disconnect_gmail(
    user=Depends(get_current_user),
):
    """
    Disconnect Gmail for the authenticated user.

    Existing leads are preserved.
    """

    try:

        connection = get_gmail_connection(
            user_id=str(user.id)
        )

        if not connection:

            return {
                "success": True,
                "message": "Gmail is already disconnected",
            }

        delete_gmail_connection(
            user_id=str(user.id)
        )

        return {
            "success": True,
            "message": "Gmail disconnected successfully",
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to disconnect Gmail: {str(e)}"
            ),
        )