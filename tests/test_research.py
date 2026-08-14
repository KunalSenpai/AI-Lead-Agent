from unittest.mock import MagicMock, patch

from app.models.lead import CompanyResearch
from app.tools.research import research_company


def test_company_research():

    # ---------------------------------------------------------
    # Fake research result
    # ---------------------------------------------------------

    fake_research = CompanyResearch(
        company_name="Google",
        industry="Technology",
        description=(
            "Google is a technology company providing "
            "internet-related products and services."
        ),
        products_or_services=[
            "Google Search",
            "Advertising",
            "Cloud Computing"
        ],
        target_customers=(
            "Consumers, businesses, and advertisers"
        ),
        company_size=None,
        summary=(
            "Google provides internet and technology "
            "services to consumers and businesses."
        ),
        source_urls=[
            "https://www.google.com"
        ]
    )

    # ---------------------------------------------------------
    # Create fake Gemini response
    # ---------------------------------------------------------

    fake_response = MagicMock()

    fake_response.text = fake_research.model_dump_json()

    # ---------------------------------------------------------
    # Create fake Gemini client
    # ---------------------------------------------------------

    mock_gemini_client = MagicMock()

    (
        mock_gemini_client
        .models
        .generate_content
        .return_value
    ) = fake_response

    # ---------------------------------------------------------
    # Replace real Gemini client
    # ---------------------------------------------------------

    with patch(
        "app.tools.research.gemini_client",
        mock_gemini_client
    ):

        result = research_company(
            company_name="Google",
            website="https://www.google.com"
        )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert result.company_name == "Google"

    assert result.industry == "Technology"

    assert result.description

    assert result.summary

    assert isinstance(
        result.products_or_services,
        list
    )

    assert len(
        result.products_or_services
    ) > 0

    assert isinstance(
        result.source_urls,
        list
    )

    assert len(
        result.source_urls
    ) > 0

    assert result.source_urls[0] == (
        "https://www.google.com"
    )

    # ---------------------------------------------------------
    # Make sure Gemini was actually called
    # ---------------------------------------------------------

    mock_gemini_client.models.generate_content.assert_called_once()