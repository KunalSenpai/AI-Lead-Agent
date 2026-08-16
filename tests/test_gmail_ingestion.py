from unittest.mock import patch


def test_gmail_ingestion_creates_new_lead():

    fake_message = {
        "id": "gmail-message-123",
    }

    fake_full_message = {
        "id": "gmail-message-123",
        "payload": {
            "headers": [
                {
                    "name": "From",
                    "value": "Priya Mehta <priya@techflow.com>",
                },
                {
                    "name": "Subject",
                    "value": "Interested in automation",
                },
            ],
            "body": {},
        },
    }

    parsed_email = {
        "message_id": "gmail-message-123",
        "name": "Priya Mehta",
        "email": "priya@techflow.com",
        "subject": "Interested in automation",
        "body": (
            "We are interested in automating "
            "our lead qualification process."
        ),
    }

    extracted_lead = type(
        "ExtractedLead",
        (),
        {
            "name": "Priya Mehta",
            "email": "priya@techflow.com",
            "company": "TechFlow",
            "website": None,
            "job_title": "Head of Sales",
            "message": (
                "We are interested in automating "
                "our lead qualification process."
            ),
        },
    )()

    fake_saved_lead = {
        "id": 999,
        "name": "Priya Mehta",
        "email": "priya@techflow.com",
    }

    class FakeRequest:
        def execute(self):
            return {
                "messages": [fake_message]
            }

    class FakeMessages:
        def list(self, **kwargs):
            return FakeRequest()

        def get(self, **kwargs):
            class GetRequest:
                def execute(self):
                    return fake_full_message

            return GetRequest()

    class FakeUsers:
        def messages(self):
            return FakeMessages()

    class FakeService:
        def users(self):
            return FakeUsers()

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=FakeService(),
    ), patch(
        "app.services.gmail_ingestion.parse_gmail_message",
        return_value=parsed_email,
    ), patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=True,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=None,
    ), patch(
        "app.services.gmail_ingestion.extract_lead_from_email",
        return_value=extracted_lead,
    ), patch(
        "app.services.gmail_ingestion.save_lead",
        return_value=fake_saved_lead,
    ):

        from app.services.gmail_ingestion import (
            fetch_and_create_gmail_leads,
        )

        result = fetch_and_create_gmail_leads()

    assert result["messages_checked"] == 1
    assert result["leads_created"] == 1
    assert result["duplicates_skipped"] == 0
    assert result["non_leads_skipped"] == 0

    assert result["created_leads"][0]["id"] == 999


def test_gmail_ingestion_skips_existing_lead():

    fake_message = {
        "id": "gmail-message-already-processed",
    }

    fake_full_message = {
        "id": "gmail-message-already-processed",
        "payload": {
            "headers": [],
            "body": {},
        },
    }

    existing_lead = {
        "id": 123,
        "source_type": "gmail",
        "source_id": "gmail-message-already-processed",
    }

    class FakeRequest:
        def execute(self):
            return {
                "messages": [fake_message]
            }

    class FakeMessages:
        def list(self, **kwargs):
            return FakeRequest()

        def get(self, **kwargs):
            class GetRequest:
                def execute(self):
                    return fake_full_message

            return GetRequest()

    class FakeUsers:
        def messages(self):
            return FakeMessages()

    class FakeService:
        def users(self):
            return FakeUsers()

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=FakeService(),
    ), patch(
        "app.services.gmail_ingestion.parse_gmail_message",
        return_value={
            "message_id": "gmail-message-already-processed",
            "name": "Priya Mehta",
            "email": "priya@example.com",
            "subject": "Interested in automation",
            "body": "We are interested in your solution.",
        },
    ), patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=True,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=existing_lead,
    ), patch(
        "app.services.gmail_ingestion.extract_lead_from_email"
    ) as mock_extract, patch(
        "app.services.gmail_ingestion.save_lead"
    ) as mock_save:

        from app.services.gmail_ingestion import (
            fetch_and_create_gmail_leads,
        )

        result = fetch_and_create_gmail_leads()

    assert result["messages_checked"] == 1
    assert result["leads_created"] == 0
    assert result["duplicates_skipped"] == 1

    mock_extract.assert_not_called()
    mock_save.assert_not_called()