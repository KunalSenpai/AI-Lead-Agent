import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.models.lead import (
    Lead,
    LeadAnalysis,
    LeadScore,
    CompanyResearch,
    EmailDraft
)


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


# ---------------------------------------------------------
# Create Gemini client
# ---------------------------------------------------------

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# Generate personalized email draft
# ---------------------------------------------------------

def generate_email(
    lead: Lead,
    analysis: LeadAnalysis,
    score: LeadScore,
    research: CompanyResearch
) -> EmailDraft:

    prompt = f"""
You are an expert B2B sales outreach assistant.

Your job is to create a personalized first-contact
email for the lead below.

========================
LEAD INFORMATION
========================

Name:
{lead.name}

Company:
{lead.company}

Job title:
{lead.job_title}

Original enquiry:
{lead.message}


========================
LEAD ANALYSIS
========================

Industry:
{analysis.industry}

Company size:
{analysis.company_size}

Monthly lead volume:
{analysis.lead_volume}

Problem:
{analysis.problem}

Urgency:
{analysis.urgency}


========================
LEAD SCORE
========================

Score:
{score.score}

Category:
{score.category}


========================
COMPANY RESEARCH
========================

Company:
{research.company_name}

Industry:
{research.industry}

Description:
{research.description}

Products/services:
{research.products_or_services}

Target customers:
{research.target_customers}

Research summary:
{research.summary}


========================
EMAIL REQUIREMENTS
========================

Write a concise, professional B2B outreach email.

Rules:

1. Address the person by their first name.

2. Mention the specific problem from their enquiry.

3. Explain how automation could potentially help
   with that problem.

4. Use relevant company research when appropriate.

5. Do not invent facts.

6. Do not claim that you spoke with the company,
   visited their office, or personally observed
   anything.

7. Do not mention the lead score.

8. Do not mention that AI researched the company.

9. Do not make exaggerated claims.

10. Do not sound like generic spam.

11. Keep the email relatively short.

12. Include a simple call to action.

13. This is ONLY a draft.
    It must NOT be sent automatically.

Return only:
- subject
- body
"""

    # -----------------------------------------------------
    # Ask Gemini to generate the email
    # -----------------------------------------------------

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EmailDraft
        )
    )

    # -----------------------------------------------------
    # Validate Gemini response
    # -----------------------------------------------------

    return EmailDraft.model_validate_json(
        response.text
    )