from unittest.mock import MagicMock, patch

from app.tools.gmail import send_email


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

    mock_send.return_value.execute.return_value = fake_response

    mock_service.users.return_value.messages.return_value.send = mock_send

    # ---------------------------------------------------------
    # Replace real Gmail service
    # ---------------------------------------------------------

    with patch(
        "app.tools.gmail.get_gmail_service",
        return_value=mock_service
    ):

        result = send_email(
            recipient="test@example.com",
            subject="Test Email",
            body="This is a test email."
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