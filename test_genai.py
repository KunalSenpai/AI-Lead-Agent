import os

from dotenv import load_dotenv
from google import genai

from app.models.lead import LeadAnalysis

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(
    api_key=api_key
)


lead_message = """
We are a 75-person SaaS company and receive around
300 inbound enquiries every month.

Our sales team manually reviews every enquiry and
assigns leads to different sales representatives.

This is taking several hours every day and we want
to automate lead qualification, scoring and routing.
"""


prompt = f"""
You are a sales lead analysis assistant.

Analyze the sales lead below.

Extract only information that can reasonably be
determined from the lead.

Do not invent information.

If information is unknown, use null where allowed.

Lead:
{lead_message}
"""


response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": LeadAnalysis,
    },
)


analysis = LeadAnalysis.model_validate_json(response.text)


print("----- LEAD ANALYSIS -----")
print("Industry:", analysis.industry)
print("Company size:", analysis.company_size)
print("Lead volume:", analysis.lead_volume)
print("Problem:", analysis.problem)
print("Urgency:", analysis.urgency)