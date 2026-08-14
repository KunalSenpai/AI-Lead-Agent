from app.models.lead import (
    Lead,
    LeadAnalysis,
    LeadScore,
    CompanyResearch
)

from app.tools.email import generate_email


def test_email_generation():

    lead = Lead(
        name="Priya Mehta",
        email="priya@techflow.example",
        company="Google",
        website="https://www.google.com",
        job_title="Founder & CEO",
        message="""
        We are a 75-person technology company and receive
        around 300 inbound enquiries every month.

        Our sales team manually reviews every enquiry and
        assigns leads to different representatives.

        This takes several hours every day and we want to
        automate lead qualification, scoring and routing.
        """
    )

    analysis = LeadAnalysis(
        industry="Technology",
        company_size=75,
        lead_volume=300,
        problem=(
            "Manual lead review, qualification, scoring, "
            "and routing taking several hours daily."
        ),
        urgency="medium"
    )

    score = LeadScore(
        score=85,
        category="Hot",
        reasons=[
            "Company has 75 employees",
            "High lead volume: 300 leads/month",
            "Lead indicates medium urgency",
            "Problem appears well suited to automation",
            "Contact appears to be a decision maker: Founder & CEO"
        ]
    )

    research = CompanyResearch(
        company_name="Google",
        industry="Technology",
        description=(
            "Google is a global technology company "
            "specializing in internet-related services "
            "and products."
        ),
        products_or_services=[
            "Google Search",
            "Advertising",
            "Cloud Computing",
            "Software",
            "Hardware"
        ],
        target_customers=(
            "General consumers, businesses, "
            "and advertisers worldwide"
        ),
        company_size=None,
        summary=(
            "Google provides internet-related services "
            "and products to global users and businesses."
        ),
        source_urls=[
            "https://www.google.com"
        ]
    )

    result = generate_email(
        lead=lead,
        analysis=analysis,
        score=score,
        research=research
    )

    # -----------------------------------------
    # Assertions
    # -----------------------------------------

    assert result.subject
    assert result.body

    assert len(result.subject) > 10
    assert len(result.body) > 50

    assert "Google" in result.subject
    assert "Priya" in result.body