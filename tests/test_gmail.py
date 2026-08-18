from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError

from app.tools.gmail import (
    get_gmail_service_for_user,
    send_email,
)


def test_send_email():

    # ---------------------------------------------------------
    # Fake Gmail response
    # ---------------------------------------------------------

    fake_response = {
        "id": "fake-message-id-12345"
    }

    # ---------------------------------------------------------
    # Create fake Gmail service
    # ---------------------------------------------------------

    mock_service = MagicMock()

    mock_send = MagicMock()

    mock_send.return_value.execute.return_value = (
        fake_response
    )

    mock_service.users.return_value.messages.return_value.send = (
        mock_send
    )

    # ---------------------------------------------------------
    # Replace real Gmail service
    # ---------------------------------------------------------

    with patch(
        "app.tools.gmail.get_gmail_service",
        return_value=mock_service,
    ):

        result = send_email(
            recipient="test@example.com",
            subject="Test Email",
            body="This is a test email.",
        )

    # ---------------------------------------------------------
    # Check returned response
    # ---------------------------------------------------------

    assert result["id"] == "fake-message-id-12345"

    # ---------------------------------------------------------
    # Make sure Gmail send was called exactly once
    # ---------------------------------------------------------

    mock_send.assert_called_once()

    # ---------------------------------------------------------
    # Check the arguments sent to Gmail
    # ---------------------------------------------------------

    call_kwargs = mock_send.call_args.kwargs

    assert call_kwargs["userId"] == "me"
    assert "body" in call_kwargs
    assert "raw" in call_kwargs["body"]


def test_get_gmail_service_for_user_refresh_failure():

    # ---------------------------------------------------------
    # Fake stored Gmail connection
    # ---------------------------------------------------------

    expired_token_expiry = (
        datetime.now(timezone.utc)
        - timedelta(minutes=10)
    ).isoformat()

    connection = {
        "user_id": "test-user-id",
        "gmail_email": "test@gmail.com",
        "access_token": "expired-access-token",
        "refresh_token": "revoked-refresh-token",
        "token_expiry": expired_token_expiry,
    }

    # ---------------------------------------------------------
    # Fake Google OAuth credentials file
    # ---------------------------------------------------------

    oauth_config = {
        "web": {
            "client_id": "fake-client-id",
            "client_secret": "fake-client-secret",
        }
    }

    # ---------------------------------------------------------
    # Fake Google credentials
    # ---------------------------------------------------------

    mock_credentials = MagicMock()

    mock_credentials.expired = True
    mock_credentials.refresh_token = (
        "revoked-refresh-token"
    )

    mock_credentials.refresh.side_effect = RefreshError(
        "invalid_grant"
    )

    # ---------------------------------------------------------
    # Mock dependencies
    # ---------------------------------------------------------

    with patch(
        "app.tools.gmail.get_gmail_connection",
        return_value=connection,
    ) as mock_get_connection, patch(
        "app.tools.gmail.os.path.exists",
        return_value=True,
    ), patch(
        "builtins.open",
        mock_open := MagicMock(),
    ), patch(
        "app.tools.gmail.Credentials",
        return_value=mock_credentials,
    ), patch(
        "app.tools.gmail.update_gmail_connection_tokens"
    ) as mock_update_tokens:

        mock_open.return_value.__enter__.return_value.read.return_value = (
            __import__("json").dumps(oauth_config)
        )

        with pytest.raises(
            RuntimeError
        ) as exc_info:

            get_gmail_service_for_user(
                user_id="test-user-id"
            )

    # ---------------------------------------------------------
    # Verify controlled error
    # ---------------------------------------------------------

    assert (
        str(exc_info.value)
        == (
            "Gmail authorization has expired or "
            "has been revoked. Please reconnect "
            "your Gmail account."
        )
    )

    # ---------------------------------------------------------
    # Verify correct user's connection was requested
    # ---------------------------------------------------------

    mock_get_connection.assert_called_once_with(
        user_id="test-user-id"
    )

    # ---------------------------------------------------------
    # Verify refresh was attempted
    # ---------------------------------------------------------

    mock_credentials.refresh.assert_called_once()

    # ---------------------------------------------------------
    # Failed refresh must never update stored credentials
    # ---------------------------------------------------------

    mock_update_tokens.assert_not_called()