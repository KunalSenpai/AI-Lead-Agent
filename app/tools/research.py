import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.models.lead import CompanyResearch


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


def research_company(
    company_name: str,
    website: str | None
) -> CompanyResearch:

    if not website:
        raise ValueError(
            "Company website is required for research"
        )

    prompt = f"""
You are a company research assistant.

Research the company using the provided public website.

Company:
{company_name}

Website:
{website}

Your job is to extract useful information for a sales
lead qualification system.

Find:

1. What the company does
2. Its industry
3. Its main products or services
4. Who its target customers appear to be
5. Approximate company size if it is clearly available
6. A concise business summary

Important rules:

- Only use information that can reasonably be supported
  by the provided website.
- Do not invent facts.
- If something is unknown, use null.
- Keep the description concise.
- Return the website as a source URL.
"""

    response = gemini_client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CompanyResearch,
        tools=[
            types.Tool(
                url_context=types.UrlContext()
            )
        ],
    ),
)

    return CompanyResearch.model_validate_json(
        response.text
    )