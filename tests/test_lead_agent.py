from unittest.mock import MagicMock, patch

import pytest

from app.agents.lead_agent import analyze_lead
from app.models.lead import Lead, LeadAnalysis


# ---------------------------------------------------------
# Fake lead
# ---------------------------------------------------------

def create_test_lead():

    return Lead(
        name="Vikram Rao",
        email="vikram@flowmatrix.example",
        company="FlowMatrix",
        website="https://flowmatrix.example",
        job_title="Director of Revenue Operations",
        message="""
        We are a 90-person B2B SaaS company receiving
        approximately 350 inbound enquiries every month.

        Our revenue team spends several hours each day
        manually reviewing, qualifying, and assigning
        incoming leads.

        We want to automate qualification, scoring,
        and routing.
        """
    )


# ---------------------------------------------------------
# Test 1: Successful analysis
# ---------------------------------------------------------

def test_analyze_lead_success():

    lead = create_test_lead()

    fake_analysis = LeadAnalysis(
        industry="SaaS",
        company_size=90,
        lead_volume=350,
        problem=(
            "Manual lead qualification and routing "
            "takes several hours each day."
        ),
        urgency="high"
    )

    fake_response = MagicMock()

    fake_response.text = (
        fake_analysis.model_dump_json()
    )

    mock_gemini_client = MagicMock()

    (
        mock_gemini_client
        .models
        .generate_content
        .return_value
    ) = fake_response

    with patch(
        "app.agents.lead_agent.gemini_client",
        mock_gemini_client
    ):

        result = analyze_lead(lead)

    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert isinstance(
        result,
        LeadAnalysis
    )

    assert result.industry == "SaaS"
    assert result.company_size == 90
    assert result.lead_volume == 350
    assert result.urgency == "high"

    mock_gemini_client.models.generate_content.assert_called_once()


# ---------------------------------------------------------
# Test 2: Gemini fails once, then succeeds
# ---------------------------------------------------------

def test_analyze_lead_retries_after_failure():

    lead = create_test_lead()

    fake_analysis = LeadAnalysis(
        industry="SaaS",
        company_size=90,
        lead_volume=350,
        problem="Manual lead qualification and routing.",
        urgency="high"
    )

    fake_response = MagicMock()

    fake_response.text = (
        fake_analysis.model_dump_json()
    )

    mock_gemini_client = MagicMock()

    mock_gemini_client.models.generate_content.side_effect = [
        Exception("Temporary Gemini failure"),
        fake_response
    ]

    with patch(
        "app.agents.lead_agent.gemini_client",
        mock_gemini_client
    ), patch(
        "app.agents.lead_agent.time.sleep"
    ) as mock_sleep:

        result = analyze_lead(lead)

    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert isinstance(
        result,
        LeadAnalysis
    )

    assert result.industry == "SaaS"

    assert (
        mock_gemini_client
        .models
        .generate_content
        .call_count
        == 2
    )

    mock_sleep.assert_called_once_with(2)


# ---------------------------------------------------------
# Test 3: Gemini fails three times
# ---------------------------------------------------------

def test_analyze_lead_fails_after_three_attempts():

    lead = create_test_lead()

    mock_gemini_client = MagicMock()

    mock_gemini_client.models.generate_content.side_effect = (
        Exception("Gemini unavailable")
    )

    with patch(
        "app.agents.lead_agent.gemini_client",
        mock_gemini_client
    ), patch(
        "app.agents.lead_agent.time.sleep"
    ) as mock_sleep:

        with pytest.raises(
            Exception,
            match="Gemini unavailable"
        ):

            analyze_lead(lead)

    # -----------------------------------------------------
    # Gemini should have been called exactly 3 times
    # -----------------------------------------------------

    assert (
        mock_gemini_client
        .models
        .generate_content
        .call_count
        == 3
    )

    # -----------------------------------------------------
    # Sleep should happen only between attempts
    # -----------------------------------------------------

    assert mock_sleep.call_count == 2