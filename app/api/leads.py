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
    get_gmail_service_for_user,
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


# =========================================================
# SHARED LEAD PROCESSING PIPELINE
# =========================================================


def process_lead(
    lead: Lead,
    lead_id: int,
    user_id: str,
):
    """
    Run the complete AI processing pipeline.

    Used by:
    - Manual leads
    - Gmail leads
    - Failed lead retries

    user_id is always supplied by the authenticated
    request and is passed to every database operation.
    """

    # =====================================================
    # 1. AI ANALYSIS
    # =====================================================

    try:

        analysis = analyze_lead(
            lead
        )

        logger.info(
            f"Lead {lead_id} analyzed successfully"
        )

    except Exception as e:

        logger.exception(
            f"AI analysis failed for lead {lead_id}"
        )

        raise HTTPException(
            status_code=502,
            detail=f"AI analysis failed: {str(e)}",
        )

    # =====================================================
    # 2. LEAD SCORING
    # =====================================================

    try:

        score = score_lead(
            lead,
            analysis,
        )

        logger.info(
            f"Lead {lead_id} scored "
            f"{score.score} ({score.category})"
        )

    except Exception as e:

        logger.exception(
            f"Lead scoring failed for lead {lead_id}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Lead scoring failed: {str(e)}",
        )

    # =====================================================
    # 3. COMPANY RESEARCH
    # =====================================================

    if lead.website:

        try:

            research = research_company(
                company_name=lead.company,
                website=lead.website,
            )

            logger.info(
                f"Company research completed "
                f"for lead {lead_id}"
            )

        except Exception as e:

            logger.exception(
                f"Company research failed "
                f"for lead {lead_id}"
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    f"Company research failed: {str(e)}"
                ),
            )

    else:

        logger.info(
            f"No website provided for lead {lead_id}. "
            "Skipping company research."
        )

        research = CompanyResearch(
            company_name=lead.company,
            industry=None,
            description=(
                "Company website was not provided, "
                "so detailed company research is unavailable."
            ),
            products_or_services=[],
            target_customers=None,
            company_size=None,
            summary=(
                "Company research was skipped because "
                "no website was available."
            ),
            source_urls=[],
        )

    # =====================================================
    # 4. GENERATE EMAIL
    # =====================================================

    try:

        email = generate_email(
            lead=lead,
            analysis=analysis,
            score=score,
            research=research,
        )

        logger.info(
            f"Email draft generated for lead {lead_id}"
        )

    except Exception as e:

        logger.exception(
            f"Email generation failed "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Email generation failed: {str(e)}"
            ),
        )

    # =====================================================
    # 5. SAVE PIPELINE RESULTS
    # =====================================================

    try:

        updated_lead = (
            save_analysis_score_research_and_email(
                lead_id=lead_id,
                user_id=user_id,

                # AI analysis
                industry=analysis.industry,
                company_size=analysis.company_size,
                lead_volume=analysis.lead_volume,
                problem=analysis.problem,
                urgency=analysis.urgency,

                # Score
                score=score.score,
                category=score.category,
                score_reasons=score.reasons,

                # Research
                research_data=research.model_dump(),

                # Email
                email_subject=email.subject,
                email_body=email.body,
            )
        )

    except Exception as e:

        logger.exception(
            f"Failed to save pipeline results "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save analysis, score, "
                f"research and email: {str(e)}"
            ),
        )

    # =====================================================
    # 6. RETURN PIPELINE RESULT
    # =====================================================

    return {
        "lead": updated_lead,
        "analysis": analysis.model_dump(),
        "score": score.model_dump(),
        "research": research.model_dump(),
        "email": email.model_dump(),
    }


# =========================================================
# RETRY FAILED LEAD
# =========================================================


def retry_lead(
    lead_id: int,
    user_id: str,
):
    """
    Retry the AI pipeline for a failed lead belonging
    to the authenticated user.
    """

    saved_lead = get_lead(
        lead_id=lead_id,
        user_id=user_id,
    )

    if saved_lead["email_status"] != "failed":

        raise HTTPException(
            status_code=400,
            detail="Only failed leads can be retried",
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
        user_id=user_id,
    )


# =========================================================
# CREATE MANUAL LEAD
# =========================================================


@router.post("/leads")
def create_lead(
    lead: Lead,
    user=Depends(get_current_user),
):
    """
    Create a manual lead and run it through the
    shared AI pipeline.
    """

    user_id = str(user.id)

    # =====================================================
    # 1. SAVE RAW LEAD
    # =====================================================

    try:

        saved_lead = save_lead(
            name=lead.name,
            email=lead.email,
            company=lead.company,
            website=lead.website,
            job_title=lead.job_title,
            message=lead.message,
            user_id=user_id,
        )

    except Exception as e:

        logger.exception(
            "Failed to save manual lead"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save lead: {str(e)}",
        )

    lead_id = saved_lead["id"]

    logger.info(
        f"Manual lead {lead_id} created "
        f"for company {lead.company}"
    )

    # =====================================================
    # 2. RUN SHARED PIPELINE
    # =====================================================

    try:

        return process_lead(
            lead=lead,
            lead_id=lead_id,
            user_id=user_id,
        )

    except HTTPException:

        try:

            update_email_status(
                lead_id=lead_id,
                status="failed",
                user_id=user_id,
            )

        except Exception:

            logger.exception(
                f"Failed to mark lead "
                f"{lead_id} as failed"
            )

        raise

    except Exception as e:

        logger.exception(
            f"Lead processing failed "
            f"for manual lead {lead_id}"
        )

        try:

            update_email_status(
                lead_id=lead_id,
                status="failed",
                user_id=user_id,
            )

        except Exception:

            logger.exception(
                f"Failed to mark lead "
                f"{lead_id} as failed"
            )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Lead processing failed: {str(e)}"
            ),
        )


# =========================================================
# GET ALL LEADS
# =========================================================


@router.get("/leads")
def get_all_leads(
    status: str | None = None,
    user=Depends(get_current_user),
):

    user_id = str(user.id)

    try:

        leads = list_leads(
            user_id=user_id,
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


# =========================================================
# GET SINGLE LEAD
# =========================================================


@router.get("/leads/{lead_id}")
def get_lead_by_id(
    lead_id: int,
    user=Depends(get_current_user),
):

    user_id = str(user.id)

    try:

        lead = get_lead(
            lead_id=lead_id,
            user_id=user_id,
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    return {
        "lead": lead
    }


# =========================================================
# APPROVE / REJECT EMAIL
# =========================================================


@router.post("/leads/{lead_id}/approve")
def approve_or_reject_email(
    lead_id: int,
    payload: dict,
    user=Depends(get_current_user),
):
    """
    Approve or reject an email draft.

    Expected body:

        {
            "approved": true
        }

    or:

        {
            "approved": false
        }
    """

    user_id = str(user.id)

    # =====================================================
    # 1. GET LEAD
    # =====================================================

    try:

        lead = get_lead(
            lead_id=lead_id,
            user_id=user_id,
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # =====================================================
    # 2. CHECK CURRENT STATUS
    # =====================================================

    if lead["email_status"] != "pending_approval":

        raise HTTPException(
            status_code=400,
            detail=(
                "Email cannot be approved or rejected "
                "because its current status is "
                f"'{lead['email_status']}'."
            ),
        )

    # =====================================================
    # 3. READ APPROVAL VALUE
    # =====================================================

    approved = payload.get(
        "approved"
    )

    if not isinstance(
        approved,
        bool,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "'approved' must be either "
                "true or false."
            ),
        )

    # =====================================================
    # 4. DETERMINE STATUS
    # =====================================================

    status = (
        "approved"
        if approved
        else "rejected"
    )

    # =====================================================
    # 5. SAVE STATUS
    # =====================================================

    try:

        updated_lead = update_email_status(
            lead_id=lead_id,
            status=status,
            user_id=user_id,
        )

    except Exception as e:

        logger.exception(
            f"Failed to update email status "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update email status: "
                f"{str(e)}"
            ),
        )

    logger.info(
        f"Lead {lead_id} email status changed "
        f"to {status}"
    )

    return {
        "message": (
            "Email approved successfully"
            if approved
            else "Email rejected successfully"
        ),
        "lead": updated_lead,
    }


# =========================================================
# EDIT EMAIL
# =========================================================


@router.patch("/leads/{lead_id}/email")
def edit_email(
    lead_id: int,
    email: EmailEdit,
    user=Depends(get_current_user),
):
    """
    Update an email draft.

    Editing an email returns it to pending_approval.
    """

    user_id = str(user.id)

    # -----------------------------------------------------
    # Get lead belonging to authenticated user
    # -----------------------------------------------------

    try:

        lead = get_lead(
            lead_id=lead_id,
            user_id=user_id,
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # -----------------------------------------------------
    # Only pending emails can be edited
    # -----------------------------------------------------

    if lead["email_status"] != "pending_approval":

        raise HTTPException(
            status_code=400,
            detail=(
                "Email can only be edited when "
                "its status is 'pending_approval'. "
                f"Current status: {lead['email_status']}"
            ),
        )

    # -----------------------------------------------------
    # Update email
    # -----------------------------------------------------

    try:

        updated_lead = update_email_draft(
            lead_id=lead_id,
            subject=email.subject,
            body=email.body,
            user_id=user_id,
        )

    except Exception as e:

        logger.exception(
            f"Failed to update email "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update email: {str(e)}"
            ),
        )

    # -----------------------------------------------------
    # Return updated lead
    # -----------------------------------------------------

    return updated_lead


# =========================================================
# SEND EMAIL
# =========================================================


@router.post("/leads/{lead_id}/send")
def send_lead_email(
    lead_id: int,
    user=Depends(get_current_user),
):
    """
    Send an approved email using the authenticated
    user's connected Gmail account.
    """

    user_id = str(user.id)

    # =====================================================
    # 1. GET USER'S LEAD
    # =====================================================

    try:

        lead = get_lead(
            lead_id=lead_id,
            user_id=user_id,
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # =====================================================
    # PREVENT DUPLICATE SEND
    # =====================================================

    if (
        lead.get("email_status") == "sent"
        or lead.get("gmail_message_id")
    ):
        logger.warning(
            f"Duplicate email send attempted "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "An email has already been sent "
                "for this lead."
            ),
        )


    # =====================================================
    # REQUIRE APPROVAL
    # =====================================================

    if lead.get("email_status") != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                "Email cannot be sent. "
                f"Current status is "
                f"'{lead.get('email_status')}'. "
                "Email must be approved first."
            ),
        )
    # =====================================================
    # 4. VALIDATE EMAIL CONTENT
    # =====================================================

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

    # =====================================================
    # 5. SEND THROUGH GMAIL
    # =====================================================

    try:

        gmail_result = send_email(
            recipient=lead["email"],
            subject=lead["email_subject"],
            body=lead["email_body"],
            user_id=user_id,
        )

    except Exception as e:

        logger.exception(
            f"Failed to send email "
            f"for lead {lead_id}"
        )

        raise HTTPException(
            status_code=502,
            detail=f"Failed to send email: {str(e)}",
        )

    # =====================================================
    # 6. VALIDATE GMAIL RESPONSE
    # =====================================================

    if not isinstance(gmail_result, dict):

        raise HTTPException(
            status_code=502,
            detail=(
                "Gmail returned an invalid response "
                "after sending the email."
            ),
        )

    gmail_message_id = gmail_result.get("id")

    if not gmail_message_id or not isinstance(
        gmail_message_id,
        str,
    ):

        raise HTTPException(
            status_code=502,
            detail=(
                "Gmail accepted the send request "
                "but did not return a valid message ID."
            ),
        )

    # =====================================================
    # 7. MARK AS SENT
    # =====================================================

    try:

        updated_lead = mark_email_as_sent(
            lead_id=lead_id,
            user_id=user_id,
            gmail_message_id=gmail_message_id,
        )

    except Exception as e:

        logger.exception(
            f"Email was sent but database update "
            f"failed for lead {lead_id}. "
            f"Gmail message ID: {gmail_message_id}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Email was sent, but the database "
                "could not be updated: "
                f"{str(e)}"
            ),
        )

    logger.info(
        f"Email sent successfully "
        f"for lead {lead_id}"
    )

    return {
        "message": "Email sent successfully",
        "gmail_message_id": gmail_message_id,
        "lead": updated_lead,
    }

# =========================================================
# GMAIL SYNC
# =========================================================


@router.post("/gmail/sync")
def sync_gmail(
    user=Depends(get_current_user),
):
    """
    Sync unread Gmail messages for the authenticated
    user, create potential leads, and run them through
    the AI pipeline.

    Ingestion failures are preserved separately from
    lead-processing failures.
    """

    user_id = str(user.id)

    try:

        # =================================================
        # 1. GET USER'S GMAIL SERVICE
        # =================================================

        gmail_service = get_gmail_service_for_user(
            user_id=user_id,
        )

        # =================================================
        # 2. INGEST GMAIL
        # =================================================

        ingestion_result = (
            fetch_and_create_gmail_leads(
                service=gmail_service,
                user_id=user_id,
            )
        )

        processed_leads = []
        failed_leads = []

        # =================================================
        # 3. PROCESS NEW LEADS
        # =================================================

        for saved_lead in ingestion_result.get(
            "created_leads",
            [],
        ):

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
                    lead_id=saved_lead["id"],
                    user_id=user_id,
                )

                # =========================================
                # Mark Gmail message as READ only after
                # successful AI processing.
                # =========================================

                try:

                    mark_message_as_read(
                        service=gmail_service,
                        message_id=saved_lead[
                            "source_id"
                        ],
                    )

                    logger.info(
                        "Gmail message marked as read "
                        f"after successful processing: "
                        f"{saved_lead['source_id']}"
                    )

                except Exception:

                    logger.exception(
                        "Failed to mark Gmail message "
                        f"{saved_lead['source_id']} as read"
                    )

                processed_leads.append(
                    result
                )

            except Exception as e:

                logger.exception(
                    "Gmail lead processing failed "
                    f"for lead {saved_lead['id']}"
                )

                # =========================================
                # Mark lead failed.
                #
                # Gmail message remains unread so a future
                # sync can retry it.
                # =========================================

                try:

                    update_email_status(
                        lead_id=saved_lead["id"],
                        status="failed",
                        user_id=user_id,
                    )

                except Exception:

                    logger.exception(
                        "Failed to mark Gmail lead "
                        f"{saved_lead['id']} as failed"
                    )

                failed_leads.append({
                    "lead_id": saved_lead["id"],
                    "error": str(e),
                })

        # =================================================
        # 4. RETURN COMPLETE SYNC RESULT
        # =================================================
        #
        # Preserve failed_messages from ingestion.
        # This is different from failed_leads:
        #
        # failed_messages = Gmail messages that could not
        #                    be parsed/ingested
        #
        # failed_leads    = messages successfully converted
        #                    to leads but whose AI pipeline
        #                    subsequently failed
        # =================================================

        return {
            "success": True,

            "messages_checked": (
                ingestion_result.get(
                    "messages_checked",
                    0,
                )
            ),

            "leads_created": (
                ingestion_result.get(
                    "leads_created",
                    0,
                )
            ),

            "duplicates_skipped": (
                ingestion_result.get(
                    "duplicates_skipped",
                    0,
                )
            ),

            "non_leads_skipped": (
                ingestion_result.get(
                    "non_leads_skipped",
                    0,
                )
            ),

            "failed_messages": (
                ingestion_result.get(
                    "failed_messages",
                    [],
                )
            ),

            "processed_leads": processed_leads,

            "failed_leads": failed_leads,
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.exception(
            "Gmail sync failed"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Gmail sync failed: {str(e)}",
        )
@router.post("/leads/{lead_id}/retry")
def retry_failed_lead(
    lead_id: int,
    user=Depends(get_current_user),
):

    user_id = str(user.id)

    try:

        return retry_lead(
            lead_id=lead_id,
            user_id=user_id,
        )

    except HTTPException:

        raise

    except Exception as e:

        logger.exception(
            f"Failed to retry lead {lead_id}"
        )

        try:

            update_email_status(
                lead_id=lead_id,
                status="failed",
                user_id=user_id,
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


# =========================================================
# AUTHENTICATED USER
# =========================================================


@router.get("/auth/me")
def get_authenticated_user(
    user=Depends(get_current_user),
):

    return {
        "id": user.id,
        "email": user.email,
    }