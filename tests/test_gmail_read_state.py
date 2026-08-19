from unittest.mock import MagicMock, patch

from app.services.gmail_ingestion import fetch_and_create_gmail_leads


def make_gmail_message(message_id: str):
    return {
        "id": message_id,
        "threadId": message_id,
    }


def make_full_gmail_message():
    return {
        "id": "test-message-123",
        "payload": {
            "headers": [
                {
                    "name": "From",
                    "value": "Alex <alex@example.com>",
                },
                {
                    "name": "Subject",
                    "value": "Interested in automating lead qualification",
                },
            ],
            "body": {
                "data": "",
            },
        },
    }
def test_existing_successful_lead_is_marked_read():

    service = MagicMock()

    service.users().messages().list().execute.return_value = {
        "messages": [
            make_gmail_message("test-message-123")
        ]
    }

    service.users().messages().get().execute.return_value = (
        make_full_gmail_message()
    )

    existing_lead = {
        "id": 28,
        "email_status": "pending_approval",
        "source_type": "gmail",
        "source_id": "test-message-123",
    }

    with patch(
        "app.services.gmail_ingestion.parse_gmail_message"
    ) as mock_parse, patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=True,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=existing_lead,
    ), patch(
        "app.services.gmail_ingestion.mark_message_as_read"
    ) as mock_mark_read:

        mock_parse.return_value = {
            "sender_name": "Alex",
            "sender_email": "alex@example.com",
            "subject": "Interested in automating lead qualification",
            "body": "We receive 200 enquiries every month.",
        }

        result = fetch_and_create_gmail_leads(
            service=service
        )

    assert result["duplicates_skipped"] == 1

    mock_mark_read.assert_called_once_with(
        service=service,
        message_id="test-message-123",
    )

def test_existing_failed_lead_is_not_marked_read():

    service = MagicMock()

    service.users().messages().list().execute.return_value = {
        "messages": [
            make_gmail_message("failed-message-456")
        ]
    }

    service.users().messages().get().execute.return_value = (
        make_full_gmail_message()
    )

    existing_lead = {
        "id": 29,
        "email_status": "failed",
        "source_type": "gmail",
        "source_id": "failed-message-456",
    }

    with patch(
        "app.services.gmail_ingestion.parse_gmail_message"
    ) as mock_parse, patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=True,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=existing_lead,
    ), patch(
        "app.services.gmail_ingestion.mark_message_as_read"
    ) as mock_mark_read:

        mock_parse.return_value = {
            "sender_name": "Alex",
            "sender_email": "alex@example.com",
            "subject": "Interested in automating lead qualification",
            "body": "We receive 200 enquiries every month.",
        }

        result = fetch_and_create_gmail_leads(
            service=service
        )

    assert result["duplicates_skipped"] == 1

    mock_mark_read.assert_not_called()

def test_non_lead_is_not_marked_read():

    service = MagicMock()

    service.users().messages().list().execute.return_value = {
        "messages": [
            make_gmail_message(
                "non-lead-message-789"
            )
        ]
    }

    service.users().messages().get().execute.return_value = (
        make_full_gmail_message()
    )

    with patch(
        "app.services.gmail_ingestion.parse_gmail_message"
    ) as mock_parse, patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=False,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=None,
    ), patch(
        "app.services.gmail_ingestion.mark_message_as_read"
    ) as mock_mark_read, patch(
        "app.services.gmail_ingestion.save_lead"
    ) as mock_save:

        mock_parse.return_value = {
            "sender_name": "Alex",
            "sender_email": "alex@example.com",
            "subject": "Newsletter",
            "body": "This is not a sales lead.",
        }

        result = fetch_and_create_gmail_leads(
            service=service
        )

    assert result["messages_checked"] == 1

    assert result["non_leads_skipped"] == 1

    assert result["leads_created"] == 0

    assert result["duplicates_skipped"] == 0

    mock_mark_read.assert_not_called()

    mock_save.assert_not_called()