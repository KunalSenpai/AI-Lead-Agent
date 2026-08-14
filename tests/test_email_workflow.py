from unittest.mock import patch

import pytest

from app.api.leads import send_lead_email


# ---------------------------------------------------------
# Helper: create a fake lead
# ---------------------------------------------------------

def make_lead(status="approved"):

    return {
        "id": 123,
        "name": "Vikram Rao",
        "email": "vikram@flowmatrix.example",
        "company": "FlowMatrix",
        "email_subject": "Automating inbound lead routing",
        "email_body": "Hi Vikram, this is a test email.",
        "email_status": status,
    }


# ---------------------------------------------------------
# Test 1: Pending approval cannot be sent
# ---------------------------------------------------------

def test_pending_approval_cannot_send():

    fake_lead = make_lead(
        status="pending_approval"
    )

    with patch(
        "app.api.leads.get_lead",
        return_value=fake_lead
    ), patch(
        "app.api.leads.send_email"
    ) as mock_send:

        with pytest.raises(Exception) as exc:

            send_lead_email(123)

    assert "approved first" in str(exc.value.detail)

    mock_send.assert_not_called()


# ---------------------------------------------------------
# Test 2: Rejected email cannot be sent
# ---------------------------------------------------------

def test_rejected_email_cannot_send():

    fake_lead = make_lead(
        status="rejected"
    )

    with patch(
        "app.api.leads.get_lead",
        return_value=fake_lead
    ), patch(
        "app.api.leads.send_email"
    ) as mock_send:

        with pytest.raises(Exception) as exc:

            send_lead_email(123)

    assert "approved first" in str(exc.value.detail)

    mock_send.assert_not_called()


# ---------------------------------------------------------
# Test 3: Already sent email cannot be sent again
# ---------------------------------------------------------

def test_already_sent_email_cannot_send_again():

    fake_lead = make_lead(
        status="sent"
    )

    with patch(
        "app.api.leads.get_lead",
        return_value=fake_lead
    ), patch(
        "app.api.leads.send_email"
    ) as mock_send:

        with pytest.raises(Exception) as exc:

            send_lead_email(123)

    assert "already been sent" in str(exc.value.detail)

    mock_send.assert_not_called()


# ---------------------------------------------------------
# Test 4: Approved email is sent
# ---------------------------------------------------------

def test_approved_email_is_sent():

    fake_lead = make_lead(
        status="approved"
    )

    fake_gmail_result = {
        "id": "fake-gmail-message-id"
    }

    fake_updated_lead = {
        **fake_lead,
        "email_status": "sent"
    }

    with patch(
        "app.api.leads.get_lead",
        return_value=fake_lead
    ), patch(
        "app.api.leads.send_email",
        return_value=fake_gmail_result
    ) as mock_send, patch(
        "app.api.leads.mark_email_as_sent",
        return_value=fake_updated_lead
    ) as mock_mark_sent:

        result = send_lead_email(123)

    # -----------------------------------------------------
    # Gmail should have been called
    # -----------------------------------------------------

    mock_send.assert_called_once_with(
        recipient="vikram@flowmatrix.example",
        subject="Automating inbound lead routing",
        body="Hi Vikram, this is a test email."
    )

    # -----------------------------------------------------
    # Database should mark email as sent
    # -----------------------------------------------------

    mock_mark_sent.assert_called_once_with(123)

    # -----------------------------------------------------
    # Check endpoint response
    # -----------------------------------------------------

    assert result["message"] == (
        "Email sent successfully"
    )

    assert result["gmail_message_id"] == (
        "fake-gmail-message-id"
    )

def test_gmail_failure_does_not_mark_email_as_sent():

    fake_lead = make_lead(
        status="approved"
    )

    with patch(
        "app.api.leads.get_lead",
        return_value=fake_lead
    ), patch(
        "app.api.leads.send_email",
        side_effect=Exception("Gmail service unavailable")
    ) as mock_send, patch(
        "app.api.leads.mark_email_as_sent"
    ) as mock_mark_sent:

        with pytest.raises(Exception) as exc:

            send_lead_email(123)

    # -----------------------------------------------------
    # Gmail was attempted
    # -----------------------------------------------------

    mock_send.assert_called_once()

    # -----------------------------------------------------
    # Database MUST NOT mark email as sent
    # -----------------------------------------------------

    mock_mark_sent.assert_not_called()

    # -----------------------------------------------------
    # Correct error should be returned
    # -----------------------------------------------------

    assert exc.value.status_code == 502

    assert "Gmail service unavailable" in (
        exc.value.detail
    )