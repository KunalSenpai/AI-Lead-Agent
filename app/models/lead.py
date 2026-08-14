from typing import Optional

from pydantic import BaseModel


class Lead(BaseModel):
    name: str
    email: str
    company: str
    website: Optional[str] = None
    job_title: Optional[str] = None
    message: str

class LeadAnalysis(BaseModel):
    industry: str
    company_size: int | None
    lead_volume: int | None
    problem: str
    urgency: str

class LeadScore(BaseModel):
    score: int
    category: str
    reasons: list[str]

class CompanyResearch(BaseModel):
    company_name: str
    industry: str | None = None
    description: str
    products_or_services: list[str]
    target_customers: str | None = None
    company_size: int | None = None
    summary: str
    source_urls: list[str]

class EmailDraft(BaseModel):
    subject: str
    body: str

class ApprovalRequest(BaseModel):
    approved: bool

class EmailEdit(BaseModel):
    subject: str
    body: str