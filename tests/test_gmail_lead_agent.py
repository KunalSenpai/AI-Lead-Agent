from unittest.mock import patch, MagicMock

from app.agents.gmail_lead_agent import (
    extract_lead_from_email,
)


def test_extract_lead_from_email():

    fake_email = {
        "name": "Priya Mehta",
        "email": "priya@techflow.com",
        "subject": "Interested in lead automation",
        "body": (
            "Hi, I am Priya, Head of Sales at TechFlow. "
            "We receive around 300 enquiries every month "
            "and are interested in automating qualification."
        ),
    }

    fake_response = MagicMock()

    fake_response.text = """
    {
        "name": "Priya Mehta",
        "email": "priya@techflow.com",
        "company": "TechFlow",
        "website": null,
        "job_title": "Head of Sales",
        "message": "We receive around 300 enquiries every month and are interested in automating qualification."
    }
    """

    with patch(
        "app.agents.gmail_lead_agent.gemini_client.models.generate_content",
        return_value=fake_response,
    ):

        result = extract_lead_from_email(fake_email)

    assert result.name == "Priya Mehta"
    assert result.email == "priya@techflow.com"
    assert result.company == "TechFlow"
    assert result.job_title == "Head of Sales"
    assert result.website is None