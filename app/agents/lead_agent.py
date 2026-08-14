import os
import time
import logging

from dotenv import load_dotenv
from google import genai

from app.models.lead import Lead, LeadAnalysis


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY was not found in .env")


# ---------------------------------------------------------
# Create Gemini client
# ---------------------------------------------------------

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# Analyze lead
# ---------------------------------------------------------

def analyze_lead(lead: Lead) -> LeadAnalysis:

    prompt = f"""
You are an AI sales lead qualification assistant.

Analyze the following sales lead.

Extract information that can reasonably be determined
from the information provided.

Important rules:

- Do not invent information.
- If information is unknown, use null where allowed.
- Keep the problem description concise.
- Classify urgency as low, medium, or high.

Lead information:

Name: {lead.name}
Company: {lead.company}
Website: {lead.website}
Job title: {lead.job_title}

Message:
{lead.message}
"""

    # -----------------------------------------------------
    # Gemini request with up to 3 attempts
    # -----------------------------------------------------

    for attempt in range(3):

        try:

            logger.info(
                f"Calling Gemini for lead analysis "
                f"(attempt {attempt + 1}/3)"
            )

            response = gemini_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": LeadAnalysis,
                },
            )

            analysis = LeadAnalysis.model_validate_json(
                response.text
            )

            logger.info(
                "Gemini lead analysis completed successfully"
            )

            return analysis

        except Exception as e:

            logger.warning(
                f"Gemini attempt {attempt + 1}/3 failed: {str(e)}"
            )

            # If this was the third and final attempt,
            # let the error go back to FastAPI.
            if attempt == 2:
                logger.error(
                    "All Gemini analysis attempts failed"
                )
                raise

            # Wait before trying again.
            time.sleep(2)