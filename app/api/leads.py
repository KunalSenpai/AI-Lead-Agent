import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.lead import (
    Lead,
    EmailEdit,
    CompanyResearch,
)
from app.core.auth import get_current_user
from app.agents.lead_agent import analyze_lead
from app.services.scoring import score_lead

from app.tools.research import research_company
from app.tools.email import generate_email
from app.tools.gmail import (
    send_email,
    get_gmail_service,
    mark_message_as_read,
)

from app.services.gmail_ingestion import (
    fetch_and_create_gmail_leads,
)

from app.tools.database import (
    save_lead,
    save_analysis_score_research_and_email,
    get_lead,
    list_leads,
    update_email_status,
    update_email_draft,
    mark_email_as_sent,
)

logger = logging.getLogger(__name__)

router = APIRouter()

def process_lead(lead: Lead, lead_id: int):
    """
    Run the complete AI processing pipeline for a lead.

    This is shared by:
    - Manual lead creation
    - Gmail lead ingestion
    """


    # -----------------------------------------
    # Step 1: Analyze lead
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
    # Step 2: Score lead
    # -----------------------------------------

    try:
        score = score_lead(
            lead,
            analysis
        )

        logger.info(
            f"Lead {lead_id} scored "
            f"{score.score} ({score.category})"
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
    # Step 3: Research company
    # -----------------------------------------

    if lead.website:

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

    else:

        logger.info(
            f"No website provided for lead {lead_id}. "
            "Skipping company research."
        )

        research = CompanyResearch(
            company_name=lead.company,
            industry=None,
            description="Company website was not provided, so detailed company research is unavailable.",
            products_or_services=[],
            target_customers=None,
            company_size=None,
            summary="Company research was skipped because no website was available.",
            source_urls=[]
        )

    # -----------------------------------------
    # Step 4: Generate email
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
        logger.error(
            f"Email generation failed for lead {lead_id}: {str(e)}"
        )

        raise HTTPException(
            status_code=502,
            detail=f"Email generation failed: {str(e)}"
        )

    # -----------------------------------------
    # Step 5: Save results
    # -----------------------------------------

    try:
        updated_lead = (
            save_analysis_score_research_and_email(
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
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save analysis, score, "
                f"research and email: {str(e)}"
            )
        )

    return {
        "lead": updated_lead,
        "analysis": analysis.model_dump(),
        "score": score.model_dump(),
        "research": research.model_dump(),
        "email": email.model_dump()
    }

def retry_lead(
    lead_id: int,
    user_id: str,
):
    """
    Re-run the AI pipeline for an existing failed lead
    belonging to the authenticated user.
    """

    saved_lead = get_lead(
        lead_id=lead_id,
        user_id=user_id,
    )

    if saved_lead["email_status"] != "failed":
        raise HTTPException(
            status_code=400,
            detail="Only failed leads can be retried"
        )

    lead = Lead(
        name=saved_lead["name"],
        email=saved_lead["email"],
        company=saved_lead["company"],
        website=saved_lead.get("website"),
        job_title=saved_lead.get("job_title"),
        message=saved_lead["message"],
    )

    return process_lead(
        lead=lead,
        lead_id=lead_id,
    )

@router.post("/leads")
def create_lead(
    lead: Lead,
    user=Depends(get_current_user),
    ):

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
            message=lead.message,
            user_id=user.id,
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

@router.get("/leads")
def get_all_leads(
    status: str | None = None,
    user=Depends(get_current_user),
):
    try:
        leads = list_leads(
            user_id=user.id,
            status=status,
        )

        return {
            "leads": leads
        }

    except Exception as e:
        logger.exception(
            "Failed to fetch leads"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/leads/{lead_id}")
def get_lead_by_id(
    lead_id: int,
    user=Depends(get_current_user),
):
    try:
        lead = get_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Lead not found: {str(e)}"
        )

    return {
        "lead": lead
    }

@router.post("/leads/{lead_id}/approve")
def approve_email(
    lead_id: int,
    user=Depends(get_current_user),
):
    try:
        lead = get_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if lead["email_status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                "Email cannot be approved because "
                f"its current status is "
                f"'{lead['email_status']}'"
            ),
        )

    try:
        updated_lead = update_email_status(
            lead_id=lead_id,
            status="approved",
            user_id=user.id,
        )

        logger.info(
            f"Email approved for lead {lead_id}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve email: {str(e)}",
        )

    return {
        "message": "Email approved successfully",
        "lead": updated_lead,
    }

@router.post("/leads/{lead_id}/reject")
def reject_email(
    lead_id: int,
    user=Depends(get_current_user),
):
    try:
        lead = get_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    if lead["email_status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                "Email cannot be rejected because "
                f"its current status is "
                f"'{lead['email_status']}'"
            ),
        )

    try:
        updated_lead = update_email_status(
            lead_id=lead_id,
            status="rejected",
            user_id=user.id,
        )

        logger.info(
            f"Email rejected for lead {lead_id}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject email: {str(e)}",
        )

    return {
        "message": "Email rejected successfully",
        "lead": updated_lead,
    }

@router.put("/leads/{lead_id}/email")
def edit_email(
    lead_id: int,
    email: EmailEdit,
    user=Depends(get_current_user),
):
    # -----------------------------------------
    # Step 1: Find the user's lead
    # -----------------------------------------

    try:
        lead = get_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
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
            ),
        )

    # -----------------------------------------
    # Step 3: Save edited email
    # -----------------------------------------

    try:
        updated_lead = update_email_draft(
            lead_id=lead_id,
            subject=email.subject,
            body=email.body,
            user_id=user.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update email: {str(e)}",
        )

    # -----------------------------------------
    # Step 4: Return updated lead
    # -----------------------------------------

    return {
        "message": "Email draft updated successfully",
        "lead": updated_lead,
    }

@router.post("/leads/{lead_id}/send")
def send_lead_email(
    lead_id: int,
    user=Depends(get_current_user),
):
    # -----------------------------------------
    # Step 1: Get the user's lead
    # -----------------------------------------

    try:
        lead = get_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # -----------------------------------------
    # Step 2: SAFETY CHECK
    # -----------------------------------------

    if lead["email_status"] == "sent":
        logger.warning(
            f"Duplicate email send attempted "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=400,
            detail="Email has already been sent.",
        )

    if lead["email_status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                "Email cannot be sent. "
                f"Current status is "
                f"'{lead['email_status']}'. "
                "Email must be approved first."
            ),
        )

    # -----------------------------------------
    # Step 3: Check email exists
    # -----------------------------------------

    if not lead.get("email_subject"):
        raise HTTPException(
            status_code=400,
            detail="Email subject is missing.",
        )

    if not lead.get("email_body"):
        raise HTTPException(
            status_code=400,
            detail="Email body is missing.",
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
            body=lead["email_body"],
        )

    except Exception as e:
        logger.error(
            f"Failed to send email for lead "
            f"{lead_id}: {str(e)}"
        )

        raise HTTPException(
            status_code=502,
            detail=f"Failed to send email: {str(e)}",
        )

    # -----------------------------------------
    # Step 5: Mark as sent
    # -----------------------------------------

    try:
        updated_lead = mark_email_as_sent(
            lead_id=lead_id,
            user_id=user.id,
        )

        logger.info(
            f"Email sent successfully for lead {lead_id}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Email was sent, but the database "
                "could not be updated: "
                f"{str(e)}"
            ),
        )

    # -----------------------------------------
    # Step 6: Return result
    # -----------------------------------------

    return {
        "message": "Email sent successfully",
        "gmail_message_id": gmail_result["id"],
        "lead": updated_lead,
    }

@router.post("/gmail/sync")
def sync_gmail(user=Depends(get_current_user)):
    

    try:

        gmail_service = get_gmail_service()

        ingestion_result = fetch_and_create_gmail_leads(
            service=gmail_service,
            user_id=user.id,
        )

        processed_leads = []
        failed_leads = []

        for saved_lead in ingestion_result["created_leads"]:

            lead = Lead(
                name=saved_lead["name"],
                email=saved_lead["email"],
                company=saved_lead["company"],
                website=saved_lead.get("website"),
                job_title=saved_lead.get("job_title"),
                message=saved_lead["message"],
            )

            try:

                result = process_lead(
                    lead=lead,
                    lead_id=saved_lead["id"]
                )

                try:

                    mark_message_as_read(
                        service=gmail_service,
                        message_id=saved_lead["source_id"]
                    )

                except Exception:

                    logger.exception(
                        f"Failed to mark Gmail message "
                        f"{saved_lead['source_id']} as read"
                    )

                processed_leads.append(
                    result
                )

            except Exception as e:

                logger.exception(
                    f"Gmail lead processing failed "
                    f"for lead {saved_lead['id']}"
                )

                try:

                   update_email_status(
                        lead_id=saved_lead["id"],
                        status="failed",
                        user_id=user.id,
                    )

                except Exception:

                    logger.exception(
                        f"Failed to mark lead "
                        f"{saved_lead['id']} as failed"
                    )

                failed_leads.append({
                    "lead_id": saved_lead["id"],
                    "error": str(e),
                })

        return {
            "success": True,
            "messages_checked": ingestion_result[
                "messages_checked"
            ],
            "leads_created": ingestion_result[
                "leads_created"
            ],
            "duplicates_skipped": ingestion_result[
                "duplicates_skipped"
            ],
            "non_leads_skipped": ingestion_result[
                "non_leads_skipped"
            ],
            "processed_leads": processed_leads,
            "failed_leads": failed_leads,
        }

    except Exception as e:

        logger.exception(
            "Gmail sync failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Gmail sync failed"
        )

@router.post("/leads/{lead_id}/retry")
def retry_failed_lead(
    lead_id: int,
    user=Depends(get_current_user),
):
    try:
        return retry_lead(
            lead_id=lead_id,
            user_id=user.id,
        )

    except HTTPException:
        raise

    except Exception as e:

        logger.exception(
            f"Failed to retry lead {lead_id}"
        )

        # -------------------------------------------------
        # Lead was not found for this authenticated user.
        # Do not expose database details.
        # -------------------------------------------------

        if "was not found" in str(e).lower():

            raise HTTPException(
                status_code=404,
                detail="Lead not found",
            )

        # -------------------------------------------------
        # Preserve failed status only when we actually
        # have access to the lead.
        # -------------------------------------------------

        try:

            update_email_status(
                lead_id=lead_id,
                status="failed",
                user_id=user.id,
            )

        except Exception:

            logger.exception(
                f"Failed to preserve failed status "
                f"for lead {lead_id}"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Lead retry failed: {str(e)}",
        )
    
@router.get("/auth/me")
def get_authenticated_user(
    user=Depends(get_current_user),
):
    return {
        "id": user.id,
        "email": user.email,
    }