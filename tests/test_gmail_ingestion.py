from unittest.mock import patch


def make_fake_service(messages, full_messages=None, next_page_tokens=None):
    full_messages = full_messages or {}
    next_page_tokens = next_page_tokens or {}

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        def execute(self):
            return self.response

    class FakeMessages:
        def list(self, **kwargs):
            page_token = kwargs.get("pageToken")

            if page_token:
                index = int(page_token)
                response = {
                    "messages": messages[index],
                }

                next_token = next_page_tokens.get(page_token)

                if next_token:
                    response["nextPageToken"] = next_token

                return FakeRequest(response)

            response = {
                "messages": messages[0],
            }

            next_token = next_page_tokens.get("initial")

            if next_token:
                response["nextPageToken"] = next_token

            return FakeRequest(response)

        def get(self, **kwargs):
            message_id = kwargs["id"]

            return FakeRequest(
                full_messages[message_id]
            )

    class FakeUsers:
        def messages(self):
            return FakeMessages()

    class FakeService:
        def users(self):
            return FakeUsers()

    return FakeService()


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

    service = make_fake_service(
        messages=[[fake_message]],
        full_messages={
            "gmail-message-123": fake_full_message,
        },
    )

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=service,
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
        "email_status": "sent",
    }

    service = make_fake_service(
        messages=[[fake_message]],
        full_messages={
            "gmail-message-already-processed":
                fake_full_message,
        },
    )

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=service,
    ), patch(
        "app.services.gmail_ingestion.parse_gmail_message",
        return_value={
            "message_id":
                "gmail-message-already-processed",
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


def test_gmail_ingestion_processes_multiple_pages():

    first_message = {
        "id": "gmail-message-page-1",
    }

    second_message = {
        "id": "gmail-message-page-2",
    }

    full_messages = {
        "gmail-message-page-1": {
            "id": "gmail-message-page-1",
            "payload": {
                "headers": [],
                "body": {},
            },
        },
        "gmail-message-page-2": {
            "id": "gmail-message-page-2",
            "payload": {
                "headers": [],
                "body": {},
            },
        },
    }

    service = make_fake_service(
        messages=[
            [first_message],
            [second_message],
        ],
        full_messages=full_messages,
        next_page_tokens={
            "initial": "1",
        },
    )

    parsed_email = {
        "message_id": "gmail-message-page",
        "name": "Test Lead",
        "email": "test@example.com",
        "subject": "Interested",
        "body": "We need help.",
    }

    extracted_lead = type(
        "ExtractedLead",
        (),
        {
            "name": "Test Lead",
            "email": "test@example.com",
            "company": "Test Company",
            "website": None,
            "job_title": "Head of Sales",
            "message": "We need help.",
        },
    )()

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=service,
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
        side_effect=[
            {"id": 1001},
            {"id": 1002},
        ],
    ):

        from app.services.gmail_ingestion import (
            fetch_and_create_gmail_leads,
        )

        result = fetch_and_create_gmail_leads()

    assert result["messages_checked"] == 2
    assert result["leads_created"] == 2
    assert len(result["created_leads"]) == 2


def test_failed_existing_lead_is_not_marked_read():

    fake_message = {
        "id": "gmail-message-failed",
    }

    fake_full_message = {
        "id": "gmail-message-failed",
        "payload": {
            "headers": [],
            "body": {},
        },
    }

    existing_lead = {
        "id": 555,
        "source_type": "gmail",
        "source_id": "gmail-message-failed",
        "email_status": "failed",
    }

    service = make_fake_service(
        messages=[[fake_message]],
        full_messages={
            "gmail-message-failed":
                fake_full_message,
        },
    )

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=service,
    ), patch(
        "app.services.gmail_ingestion.parse_gmail_message",
        return_value={
            "message_id": "gmail-message-failed",
            "name": "Failed Lead",
            "email": "failed@example.com",
            "subject": "Need help",
            "body": "Please contact us.",
        },
    ), patch(
        "app.services.gmail_ingestion.is_potential_lead",
        return_value=True,
    ), patch(
        "app.services.gmail_ingestion.get_lead_by_source",
        return_value=existing_lead,
    ), patch(
        "app.services.gmail_ingestion.mark_message_as_read"
    ) as mock_mark_read:

        from app.services.gmail_ingestion import (
            fetch_and_create_gmail_leads,
        )

        result = fetch_and_create_gmail_leads()

    assert result["messages_checked"] == 1
    assert result["duplicates_skipped"] == 1

    mock_mark_read.assert_not_called()

def test_gmail_ingestion_continues_after_message_failure():

    first_message = {
        "id": "gmail-message-fails",
    }

    second_message = {
        "id": "gmail-message-succeeds",
    }

    full_messages = {
        "gmail-message-fails": {
            "id": "gmail-message-fails",
            "payload": {
                "headers": [],
                "body": {},
            },
        },
        "gmail-message-succeeds": {
            "id": "gmail-message-succeeds",
            "payload": {
                "headers": [],
                "body": {},
            },
        },
    }

    service = make_fake_service(
        messages=[
            [
                first_message,
                second_message,
            ]
        ],
        full_messages=full_messages,
    )

    def parse_message(full_message):

        if full_message["id"] == "gmail-message-fails":
            raise RuntimeError(
                "Failed to parse Gmail message"
            )

        return {
            "message_id": "gmail-message-succeeds",
            "name": "Successful Lead",
            "email": "success@example.com",
            "subject": "Interested in automation",
            "body": "We need help.",
        }

    extracted_lead = type(
        "ExtractedLead",
        (),
        {
            "name": "Successful Lead",
            "email": "success@example.com",
            "company": "Success Company",
            "website": None,
            "job_title": "Head of Sales",
            "message": "We need help.",
        },
    )()

    with patch(
        "app.services.gmail_ingestion.get_gmail_service",
        return_value=service,
    ), patch(
        "app.services.gmail_ingestion.parse_gmail_message",
        side_effect=parse_message,
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
        return_value={"id": 2001},
    ):

        from app.services.gmail_ingestion import (
            fetch_and_create_gmail_leads,
        )

        result = fetch_and_create_gmail_leads()

    assert result["messages_checked"] == 2

    assert result["leads_created"] == 1

    assert result["failed_messages"] == [
        {
            "message_id": "gmail-message-fails",
            "error": "Failed to parse Gmail message",
        }
    ]

    assert result["created_leads"] == [
        {"id": 2001}
    ]