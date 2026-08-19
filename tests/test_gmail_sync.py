from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.leads import sync_gmail


class FakeUser:
    id = "test-user-id"
    email = "test@example.com"


def test_gmail_sync_success():

    fake_service = object()

    ingestion_result = {
        "messages_checked": 3,
        "leads_created": 1,
        "duplicates_skipped": 1,
        "non_leads_skipped": 1,
        "failed_messages": [],
        "created_leads": [
            {
                "id": 101,
                "name": "Priya Mehta",
                "email": "priya@techflow.com",
                "company": "TechFlow",
                "website": None,
                "job_title": "Head of Sales",
                "message": "We need automation.",
                "source_type": "gmail",
                "source_id": "gmail-message-101",
            }
        ],
    }

    processed_result = {
        "id": 101,
        "email_status": "pending_approval",
    }

    with patch(
        "app.api.leads.get_gmail_service_for_user",
        return_value=fake_service,
    ) as mock_get_service, patch(
        "app.api.leads.fetch_and_create_gmail_leads",
        return_value=ingestion_result,
    ) as mock_ingestion, patch(
        "app.api.leads.process_lead",
        return_value=processed_result,
    ) as mock_process, patch(
        "app.api.leads.mark_message_as_read",
    ) as mock_mark_read:

        result = sync_gmail(
            user=FakeUser()
        )

    mock_get_service.assert_called_once_with(
        user_id="test-user-id",
    )

    mock_ingestion.assert_called_once_with(
        service=fake_service,
        user_id="test-user-id",
    )

    mock_process.assert_called_once()

    mock_mark_read.assert_called_once_with(
        service=fake_service,
        message_id="gmail-message-101",
    )

    assert result["success"] is True
    assert result["messages_checked"] == 3
    assert result["leads_created"] == 1
    assert result["duplicates_skipped"] == 1
    assert result["non_leads_skipped"] == 1

    assert result["processed_leads"] == [
        processed_result
    ]

    assert result["failed_leads"] == []


def test_gmail_sync_returns_failed_leads():

    fake_service = object()

    ingestion_result = {
        "messages_checked": 1,
        "leads_created": 1,
        "duplicates_skipped": 0,
        "non_leads_skipped": 0,
        "failed_messages": [],
        "created_leads": [
            {
                "id": 202,
                "name": "Failed Lead",
                "email": "failed@example.com",
                "company": "Failed Company",
                "website": None,
                "job_title": "Sales Director",
                "message": "We need help.",
                "source_type": "gmail",
                "source_id": "gmail-message-202",
            }
        ],
    }

    with patch(
        "app.api.leads.get_gmail_service_for_user",
        return_value=fake_service,
    ), patch(
        "app.api.leads.fetch_and_create_gmail_leads",
        return_value=ingestion_result,
    ), patch(
        "app.api.leads.process_lead",
        side_effect=Exception(
            "AI processing failed"
        ),
    ) as mock_process, patch(
        "app.api.leads.update_email_status",
    ) as mock_update_status, patch(
        "app.api.leads.mark_message_as_read",
    ) as mock_mark_read:

        result = sync_gmail(
            user=FakeUser()
        )

    mock_process.assert_called_once()

    mock_update_status.assert_called_once_with(
        lead_id=202,
        status="failed",
        user_id="test-user-id",
    )

    mock_mark_read.assert_not_called()

    assert result["success"] is True
    assert result["failed_leads"] == [
        {
            "lead_id": 202,
            "error": "AI processing failed",
        }
    ]

    assert result["processed_leads"] == []


def test_gmail_sync_returns_ingestion_failures():

    fake_service = object()

    ingestion_result = {
        "messages_checked": 2,
        "leads_created": 1,
        "duplicates_skipped": 0,
        "non_leads_skipped": 0,
        "failed_messages": [
            {
                "message_id": "gmail-message-failed",
                "error": "Failed to parse Gmail message",
            }
        ],
        "created_leads": [],
    }

    with patch(
        "app.api.leads.get_gmail_service_for_user",
        return_value=fake_service,
    ), patch(
        "app.api.leads.fetch_and_create_gmail_leads",
        return_value=ingestion_result,
    ):

        result = sync_gmail(
            user=FakeUser()
        )

    assert result["success"] is True

    assert result["messages_checked"] == 2

    assert result["leads_created"] == 1

    assert result["failed_leads"] == []

    assert result["processed_leads"] == []

    assert result["failed_messages"] == [
        {
            "message_id": "gmail-message-failed",
            "error": "Failed to parse Gmail message",
        }
    ]


def test_gmail_sync_gmail_authentication_failure():

    with patch(
        "app.api.leads.get_gmail_service_for_user",
        side_effect=RuntimeError(
            "Gmail authorization has expired or "
            "has been revoked. Please reconnect "
            "your Gmail account."
        ),
    ):

        with pytest.raises(
            HTTPException
        ) as exc_info:

            sync_gmail(
                user=FakeUser()
            )

    assert exc_info.value.status_code == 500

    assert (
        exc_info.value.detail
        == (
            "Gmail sync failed: "
            "Gmail authorization has expired or "
            "has been revoked. Please reconnect "
            "your Gmail account."
        )
    )