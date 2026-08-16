import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.models.lead import Lead


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


class GmailLeadExtraction(BaseModel):
    name: str
    email: str
    company: str | None = None
    website: str | None = None
    job_title: str | None = None
    message: str


def extract_lead_from_email(
    email_data: dict
) -> GmailLeadExtraction:

    prompt = f"""
You are extracting a potential sales lead from an
inbound email.

Extract only information that can reasonably be
determined from the email.

Do not invent information.

If the company, website, or job title cannot be
determined reliably, return null.

Email sender name:
{email_data.get("name")}

Email address:
{email_data.get("email")}

Subject:
{email_data.get("subject")}

Email body:
{email_data.get("body")}

Return:

- name
- email
- company
- website
- job_title
- message

The message should contain the useful sales enquiry
content from the email.

Do not include your own commentary.
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": GmailLeadExtraction,
        },
    )

    return GmailLeadExtraction.model_validate_json(
        response.text
    )