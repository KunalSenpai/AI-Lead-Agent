import logging
from fastapi import APIRouter, HTTPException

from app.models import lead
from app.models.lead import Lead, EmailEdit
from app.agents.lead_agent import analyze_lead
from app.services.scoring import score_lead
from app.tools.research import research_company
from app.tools.email import generate_email
from app.tools.gmail import send_email

from app.tools.database import (
    save_lead,
    save_analysis_score_research_and_email,
    get_lead,
    update_email_status,
    update_email_draft,
    mark_email_as_sent
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/leads")
def create_lead(lead: Lead):

    # -----------------------------------------
    # Step 1: Save raw lead
    # -----------------------------------------

    try:
        saved_lead = save_lead(
            name=lead.name,
            email=lead.email,
            company=lead.company,
            website=lead.website,
            job_title=lead.job_title,
            message=lead.message
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save lead: {str(e)}"
        )

    lead_id = saved_lead["id"]


    logger.info(
    f"Lead {lead_id} created for company {lead.company}"
)

    # -----------------------------------------
    # Step 2: Analyze lead with Gemini
    # -----------------------------------------

    try:
        analysis = analyze_lead(lead)

        logger.info(
    f"Lead {lead_id} analyzed successfully"
)

    except Exception as e:
        logger.error(
        f"AI analysis failed for lead {lead_id}: {str(e)}"
    )
        raise HTTPException(
            status_code=502,
            detail=f"AI analysis failed: {str(e)}"
        )

    # -----------------------------------------
    # Step 3: Score lead
    # -----------------------------------------

    try:
        score = score_lead(
            lead,
            analysis
        )
        logger.info(
    f"Lead {lead_id} scored {score.score} "
    f"({score.category})"
)
    except Exception as e:
        logger.error(
        f"Lead scoring failed for lead {lead_id}: {str(e)}"
    )
        raise HTTPException(
            status_code=500,
            detail=f"Lead scoring failed: {str(e)}"
        )

    # -----------------------------------------
    # Step 4: Research the company
    # -----------------------------------------

    try:
        research = research_company(
            company_name=lead.company,
            website=lead.website
        )
        logger.info(
    f"Company research completed for lead {lead_id}"
)

    except Exception as e:
        logger.error(
        f"Company research failed for lead {lead_id}: {str(e)}"
    )
        raise HTTPException(
            status_code=502,
            detail=f"Company research failed: {str(e)}"
        )

    # -----------------------------------------
    # Step 5: Generate personalized email
    # -----------------------------------------

    try:
        email = generate_email(
            lead=lead,
            analysis=analysis,
            score=score,
            research=research
        )
        logger.info(
    f"Email draft generated for lead {lead_id}"
)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Email generation failed: {str(e)}"
        )

    # -----------------------------------------
    # Step 6: Save everything to Supabase
    # -----------------------------------------

    try:
        updated_lead = save_analysis_score_research_and_email(
            lead_id=lead_id,

            # AI analysis
            industry=analysis.industry,
            company_size=analysis.company_size,
            lead_volume=analysis.lead_volume,
            problem=analysis.problem,
            urgency=analysis.urgency,

            # Lead score
            score=score.score,
            category=score.category,
            score_reasons=score.reasons,

            # Company research
            research_data=research.model_dump(),

            # Email draft
            email_subject=email.subject,
            email_body=email.body
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save analysis, score, "
                f"research and email: {str(e)}"
            )
        )

    # -----------------------------------------
    # Step 7: Return everything
    # -----------------------------------------

    return {
        "lead": updated_lead,
        "analysis": analysis.model_dump(),
        "score": score.model_dump(),
        "research": research.model_dump(),
        "email": email.model_dump()
    }

@router.get("/leads/{lead_id}")
def get_lead_by_id(lead_id: int):

    try:
        lead = get_lead(lead_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    return {
        "lead": lead
    }

@router.post("/leads/{lead_id}/approve")
def approve_email(lead_id: int):

    try:
        lead = get_lead(lead_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    if lead["email_status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Email cannot be approved because "
                f"its current status is "
                f"'{lead['email_status']}'"
            )
        )

    try:
        updated_lead = update_email_status(
            lead_id,
            "approved"
        )
        logger.info(
    f"Email approved for lead {lead_id}"
)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve email: {str(e)}"
        )

    return {
        "message": "Email approved successfully",
        "lead": updated_lead
    }

@router.post("/leads/{lead_id}/reject")
def reject_email(lead_id: int):

    try:
        lead = get_lead(lead_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    if lead["email_status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Email cannot be rejected because "
                f"its current status is "
                f"'{lead['email_status']}'"
            )
        )

    try:
        updated_lead = update_email_status(
            lead_id,
            "rejected"
        )
        logger.info(
    f"Email rejected for lead {lead_id}"
)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject email: {str(e)}"
        )

    return {
        "message": "Email rejected successfully",
        "lead": updated_lead
    }

@router.put("/leads/{lead_id}/email")
def edit_email(
    lead_id: int,
    email: EmailEdit
):

    # -----------------------------------------
    # Step 1: Find the lead
    # -----------------------------------------

    try:
        lead = get_lead(lead_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    # -----------------------------------------
    # Step 2: Only allow editing when
    #         email is pending approval
    # -----------------------------------------

    if lead["email_status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                "Email can only be edited when "
                "its status is 'pending_approval'. "
                f"Current status: {lead['email_status']}"
            )
        )

    # -----------------------------------------
    # Step 3: Save edited email
    # -----------------------------------------

    try:
        updated_lead = update_email_draft(
            lead_id=lead_id,
            subject=email.subject,
            body=email.body
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update email: {str(e)}"
        )

    # -----------------------------------------
    # Step 4: Return updated lead
    # -----------------------------------------

    return {
        "message": "Email draft updated successfully",
        "lead": updated_lead
    }

@router.post("/leads/{lead_id}/send")
def send_lead_email(lead_id: int):

    # -----------------------------------------
    # Step 1: Get the lead
    # -----------------------------------------

    try:
        lead = get_lead(lead_id)

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    # -----------------------------------------
    # Step 2: SAFETY CHECK
    # -----------------------------------------

    if lead["email_status"] == "sent":
        logger.warning(
        f"Duplicate email send attempted for lead {lead_id}"
    )
        raise HTTPException(
        status_code=400,
        detail="Email has already been sent."
    )

    if lead["email_status"] != "approved":
        raise HTTPException(
        status_code=400,
        detail=(
            "Email cannot be sent. "
            f"Current status is "
            f"'{lead['email_status']}'. "
            "Email must be approved first."
        )
    )
    # -----------------------------------------
    # Step 3: Check email exists
    # -----------------------------------------

    if not lead.get("email_subject"):
        raise HTTPException(
            status_code=400,
            detail="Email subject is missing."
        )

    if not lead.get("email_body"):
        raise HTTPException(
            status_code=400,
            detail="Email body is missing."
        )
        

    # -----------------------------------------
    # Step 4: Send through Gmail
    # -----------------------------------------
    logger.info(
    f"Sending email for lead {lead_id}"
)
    try:

        gmail_result = send_email(
            recipient=lead["email"],
            subject=lead["email_subject"],
            body=lead["email_body"]
        )

    except Exception as e:
        logger.error(
        f"Failed to send email for lead {lead_id}: {str(e)}"
    )
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send email: {str(e)}"
        )

    # -----------------------------------------
    # Step 5: Mark as sent
    # -----------------------------------------

    try:

        updated_lead = mark_email_as_sent(
            lead_id
        )
        logger.info(
    f"Email sent successfully for lead {lead_id}"
)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Email was sent, but the database "
                f"could not be updated: {str(e)}"
            )
        )

    # -----------------------------------------
    # Step 6: Return result
    # -----------------------------------------

    return {
        "message": "Email sent successfully",
        "gmail_message_id": gmail_result["id"],
        "lead": updated_lead
    }