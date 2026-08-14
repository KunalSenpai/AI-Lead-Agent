from app.models.lead import Lead, LeadAnalysis
from app.services.scoring import score_lead


def test_lead_scoring():

    lead = Lead(
        name="Priya Mehta",
        email="priya@techflow.example",
        company="TechFlow Solutions",
        website="https://example.com",
        job_title="Founder & CEO",
        message="""
        We are a 75-person SaaS company and receive around
        300 inbound enquiries every month.

        Our sales team manually reviews every enquiry and
        assigns leads to different sales representatives.

        This is taking several hours every day and we want
        to automate lead qualification, scoring and routing.
        """
    )

    analysis = LeadAnalysis(
        industry="SaaS",
        company_size=75,
        lead_volume=300,
        problem="Manual review and assignment of inbound enquiries",
        urgency="medium"
    )

    result = score_lead(
        lead,
        analysis
    )

    assert result.score == 85
    assert result.category == "Hot"
    assert len(result.reasons) == 5