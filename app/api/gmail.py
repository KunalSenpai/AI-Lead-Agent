import json
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

GOOGLE_CLIENT_SECRET_FILE = os.getenv(
    "GOOGLE_CLIENT_SECRET_FILE",
    "credentials/gmail_web_credentials.json",
)

GOOGLE_CLIENT_SECRET_JSON = os.getenv(
    "GOOGLE_CLIENT_SECRET_JSON"
)

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/gmail/oauth/callback",
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
# Google OAuth helpers
# ---------------------------------------------------------


def _get_google_client_config() -> dict:
    """
    Return the Google OAuth client configuration.

    Production:
        GOOGLE_CLIENT_SECRET_JSON contains the complete
        Google OAuth JSON object.

    Local development:
        GOOGLE_CLIENT_SECRET_FILE points to the local
        credentials JSON file.
    """

    if GOOGLE_CLIENT_SECRET_JSON:
        try:
            client_config = json.loads(
                GOOGLE_CLIENT_SECRET_JSON
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GOOGLE_CLIENT_SECRET_JSON contains invalid JSON"
            ) from exc

        if not isinstance(client_config, dict):
            raise RuntimeError(
                "GOOGLE_CLIENT_SECRET_JSON must contain a JSON object"
            )

        if "web" not in client_config:
            raise RuntimeError(
                "GOOGLE_CLIENT_SECRET_JSON must contain a 'web' object"
            )

        return client_config

    if not os.path.exists(
        GOOGLE_CLIENT_SECRET_FILE
    ):
        raise RuntimeError(
            "Google Web OAuth credentials file "
            "was not found at "
            f"{GOOGLE_CLIENT_SECRET_FILE}"
        )

    try:
        with open(
            GOOGLE_CLIENT_SECRET_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            client_config = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Google Web OAuth credentials file contains invalid JSON"
        ) from exc

    if not isinstance(client_config, dict):
        raise RuntimeError(
            "Google Web OAuth credentials must contain a JSON object"
        )

    if "web" not in client_config:
        raise RuntimeError(
            "Google Web OAuth credentials must contain a 'web' object"
        )

    return client_config


def _create_google_flow() -> Flow:
    """
    Create the Google OAuth flow from either:

    1. GOOGLE_CLIENT_SECRET_JSON, or
    2. GOOGLE_CLIENT_SECRET_FILE.
    """

    client_config = _get_google_client_config()

    return Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


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

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail=(
                "GOOGLE_CLIENT_ID is not configured "
                "in the backend environment"
            ),
        )

    try:
        # Validate OAuth credentials before
        # generating the authorization URL.
        _get_google_client_config()

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

        return {
            "success": True,
            "authorization_url": authorization_url,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to start Gmail OAuth: {str(e)}"
            ),
        )


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

        flow = _create_google_flow()

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
            url=(
                f"{FRONTEND_URL}"
                "/dashboard?gmail=connected"
            )
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


# ---------------------------------------------------------
# Gmail status
# ---------------------------------------------------------


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


# ---------------------------------------------------------
# Gmail disconnect
# ---------------------------------------------------------


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