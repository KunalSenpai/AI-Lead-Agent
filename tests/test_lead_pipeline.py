from unittest.mock import patch

from app.api.leads import create_lead
from app.models.lead import (
    Lead,
    LeadAnalysis,
    LeadScore,
    CompanyResearch,
    EmailDraft
)


def test_full_lead_pipeline():

    # ---------------------------------------------------------
    # Fake incoming lead
    # ---------------------------------------------------------

    lead = Lead(
        name="Vikram Rao",
        email="vikram@flowmatrix.example",
        company="FlowMatrix",
        website="https://flowmatrix.example",
        job_title="Director of Revenue Operations",
        message="""
        We are a 90-person B2B SaaS company receiving
        approximately 350 inbound enquiries every month.

        Our revenue team spends several hours every day
        manually reviewing and assigning leads.

        We want to automate lead qualification,
        scoring and routing.
        """
    )

    # ---------------------------------------------------------
    # Fake database result after raw lead is saved
    # ---------------------------------------------------------

    saved_lead = {
        "id": 999,
        "name": "Vikram Rao",
        "email": "vikram@flowmatrix.example",
        "company": "FlowMatrix",
    }

    # ---------------------------------------------------------
    # Fake Gemini analysis
    # ---------------------------------------------------------

    analysis = LeadAnalysis(
        industry="SaaS",
        company_size=90,
        lead_volume=350,
        problem=(
            "Manual lead qualification and routing "
            "takes several hours every day."
        ),
        urgency="high"
    )

    # ---------------------------------------------------------
    # Fake lead score
    # ---------------------------------------------------------

    score = LeadScore(
        score=92,
        category="Hot",
        reasons=[
            "Company has 90 employees",
            "High lead volume: 350 leads/month",
            "Lead indicates high urgency",
            "Problem appears well suited to automation",
            "Contact appears to be a decision maker"
        ]
    )

    # ---------------------------------------------------------
    # Fake company research
    # ---------------------------------------------------------

    research = CompanyResearch(
        company_name="FlowMatrix",
        industry="SaaS",
        description=(
            "FlowMatrix provides software solutions "
            "for revenue teams."
        ),
        products_or_services=[
            "Revenue automation",
            "Lead management"
        ],
        target_customers="B2B companies",
        company_size=90,
        summary=(
            "FlowMatrix provides SaaS solutions "
            "for revenue operations."
        ),
        source_urls=[
            "https://flowmatrix.example"
        ]
    )

    # ---------------------------------------------------------
    # Fake generated email
    # ---------------------------------------------------------

    email = EmailDraft(
        subject="Automating lead routing for FlowMatrix",
        body=(
            "Hi Vikram,\n\n"
            "I noticed your team handles a high volume "
            "of inbound enquiries manually.\n\n"
            "We can help automate qualification and routing."
        )
    )

    # ---------------------------------------------------------
    # Fake final database record
    # ---------------------------------------------------------

    updated_lead = {
        **saved_lead,
        "industry": "SaaS",
        "company_size": 90,
        "lead_volume": 350,
        "score": 92,
        "category": "Hot",
        "email_subject": email.subject,
        "email_body": email.body,
        "email_status": "pending_approval"
    }

    # ---------------------------------------------------------
    # Mock every external dependency
    # ---------------------------------------------------------

    with patch(
        "app.api.leads.save_lead",
        return_value=saved_lead
    ) as mock_save_lead, patch(
        "app.api.leads.analyze_lead",
        return_value=analysis
    ) as mock_analyze, patch(
        "app.api.leads.score_lead",
        return_value=score
    ) as mock_score, patch(
        "app.api.leads.research_company",
        return_value=research
    ) as mock_research, patch(
        "app.api.leads.generate_email",
        return_value=email
    ) as mock_email, patch(
        "app.api.leads.save_analysis_score_research_and_email",
        return_value=updated_lead
    ) as mock_save_all:

        result = create_lead(lead)

    # ---------------------------------------------------------
    # Verify pipeline result
    # ---------------------------------------------------------

    assert result["lead"]["id"] == 999

    assert result["analysis"] == (
        analysis.model_dump()
    )

    assert result["score"] == (
        score.model_dump()
    )

    assert result["research"] == (
        research.model_dump()
    )

    assert result["email"] == (
        email.model_dump()
    )

    # ---------------------------------------------------------
    # Verify every pipeline stage was called
    # ---------------------------------------------------------

    mock_save_lead.assert_called_once()

    mock_analyze.assert_called_once_with(
        lead
    )

    mock_score.assert_called_once_with(
        lead,
        analysis
    )

    mock_research.assert_called_once_with(
        company_name="FlowMatrix",
        website="https://flowmatrix.example"
    )

    mock_email.assert_called_once_with(
        lead=lead,
        analysis=analysis,
        score=score,
        research=research
    )

    mock_save_all.assert_called_once()
    