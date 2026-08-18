from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.leads import send_lead_email


class FakeUser:
    id = "test-user-id"
    email = "test@example.com"


def make_lead(
    status: str,
    lead_id: int = 1,
):
    return {
        "id": lead_id,
        "name": "Sarah",
        "email": "sarah@example.com",
        "company": "Acme Software",
        "website": "https://acme.example.com",
        "job_title": "Head of Sales",
        "message": (
            "We receive around 300 enquiries each month "
            "and currently qualify them manually."
        ),
        "user_id": "test-user-id",
        "email_subject": "Automating lead qualification",
        "email_body": (
            "Hi Sarah,\n\n"
            "I would be happy to show you how automated "
            "lead qualification could help your team."
        ),
        "email_status": status,
    }


def test_pending_approval_cannot_send():

    lead = make_lead("pending_approval")

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead:

        with pytest.raises(HTTPException) as exc:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert exc.value.status_code == 400

        assert (
            "approved first"
            in exc.value.detail
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )


def test_rejected_email_cannot_send():

    lead = make_lead("rejected")

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead:

        with pytest.raises(HTTPException) as exc:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert exc.value.status_code == 400

        assert (
            "approved first"
            in exc.value.detail
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )


def test_already_sent_email_cannot_send_again():

    lead = make_lead("sent")

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead:

        with pytest.raises(HTTPException) as exc:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert exc.value.status_code == 400

        assert (
            "already been sent"
            in exc.value.detail
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )


def test_approved_email_is_sent():

    lead = make_lead("approved")

    gmail_result = {
        "id": "gmail-message-123",
    }

    updated_lead = {
        **lead,
        "email_status": "sent",
        "gmail_message_id": "gmail-message-123",
    }

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead, patch(
        "app.api.leads.send_email",
        return_value=gmail_result,
    ) as mock_send_email, patch(
        "app.api.leads.mark_email_as_sent",
        return_value=updated_lead,
    ) as mock_mark_sent:

        result = send_lead_email(
            lead_id=1,
            user=FakeUser(),
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )

        mock_send_email.assert_called_once_with(
            recipient="sarah@example.com",
            subject="Automating lead qualification",
            body=(
                "Hi Sarah,\n\n"
                "I would be happy to show you how automated "
                "lead qualification could help your team."
            ),
            user_id="test-user-id",
        )

        mock_mark_sent.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
            gmail_message_id="gmail-message-123",
        )

        assert (
            result["message"]
            == "Email sent successfully"
        )

        assert (
            result["gmail_message_id"]
            == "gmail-message-123"
        )

        assert (
            result["lead"]["email_status"]
            == "sent"
        )

        assert (
            result["lead"]["gmail_message_id"]
            == "gmail-message-123"
        )


def test_gmail_failure_does_not_mark_email_as_sent():

    lead = make_lead("approved")

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead, patch(
        "app.api.leads.send_email",
        side_effect=Exception(
            "Gmail API failed"
        ),
    ) as mock_send_email, patch(
        "app.api.leads.mark_email_as_sent",
    ) as mock_mark_sent:

        with pytest.raises(HTTPException) as exc:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert exc.value.status_code == 502

        assert (
            "Gmail API failed"
            in exc.value.detail
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )

        mock_send_email.assert_called_once()

        mock_mark_sent.assert_not_called()


def test_send_email_failure_does_not_mark_lead_as_sent():

    lead = make_lead("approved")

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead, patch(
        "app.api.leads.send_email",
        side_effect=Exception(
            "Gmail API unavailable"
        ),
    ) as mock_send_email, patch(
        "app.api.leads.mark_email_as_sent",
    ) as mock_mark_sent:

        with pytest.raises(
            HTTPException
        ) as exc_info:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert exc_info.value.status_code == 502

        assert (
            exc_info.value.detail
            == "Failed to send email: Gmail API unavailable"
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )

        mock_send_email.assert_called_once_with(
            recipient="sarah@example.com",
            subject="Automating lead qualification",
            body=(
                "Hi Sarah,\n\n"
                "I would be happy to show you how automated "
                "lead qualification could help your team."
            ),
            user_id="test-user-id",
        )

        mock_mark_sent.assert_not_called()


def test_send_email_database_update_failure_after_gmail_success():

    lead = make_lead("approved")

    gmail_result = {
        "id": "gmail-message-db-failure-test",
    }

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead, patch(
        "app.api.leads.send_email",
        return_value=gmail_result,
    ) as mock_send_email, patch(
        "app.api.leads.mark_email_as_sent",
        side_effect=Exception(
            "Supabase temporarily unavailable"
        ),
    ) as mock_mark_sent:

        with pytest.raises(
            HTTPException
        ) as exc_info:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert (
            exc_info.value.status_code
            == 500
        )

        assert (
            exc_info.value.detail
            == (
                "Email was sent, but the database "
                "could not be updated: "
                "Supabase temporarily unavailable"
            )
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )

        mock_send_email.assert_called_once_with(
            recipient="sarah@example.com",
            subject="Automating lead qualification",
            body=(
                "Hi Sarah,\n\n"
                "I would be happy to show you how automated "
                "lead qualification could help your team."
            ),
            user_id="test-user-id",
        )

        mock_mark_sent.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
            gmail_message_id="gmail-message-db-failure-test",
        )


def test_send_is_blocked_when_gmail_message_id_already_exists():

    lead = {
        **make_lead("approved"),
        "gmail_message_id": "already-sent-gmail-message",
    }

    with patch(
        "app.api.leads.get_lead",
        return_value=lead,
    ) as mock_get_lead, patch(
        "app.api.leads.send_email",
    ) as mock_send_email:

        with pytest.raises(
            HTTPException
        ) as exc_info:

            send_lead_email(
                lead_id=1,
                user=FakeUser(),
            )

        assert (
            exc_info.value.status_code
            == 400
        )

        assert (
            exc_info.value.detail
            == "An email has already been sent for this lead."
        )

        mock_get_lead.assert_called_once_with(
            lead_id=1,
            user_id="test-user-id",
        )

        mock_send_email.assert_not_called()