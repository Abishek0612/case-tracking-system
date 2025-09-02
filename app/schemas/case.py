from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    CASE_NUMBER = "case_number"
    COMPLAINANT = "complainant"
    RESPONDENT = "respondent"
    COMPLAINANT_ADVOCATE = "complainant_advocate"
    RESPONDENT_ADVOCATE = "respondent_advocate"
    INDUSTRY_TYPE = "industry_type"
    JUDGE = "judge"


class CaseSearchRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., KARNATAKA)")
    commission: str = Field(..., description="Commission name")
    search_value: str = Field(..., min_length=1, description="Search value")
    
    @validator('state', 'commission', 'search_value')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class CaseResponse(BaseModel):
    case_number: str
    case_stage: str
    filing_date: str
    complainant: str
    complainant_advocate: Optional[str] = None
    respondent: str
    respondent_advocate: Optional[str] = None
    document_link: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_number": "123/2025",
                "case_stage": "Hearing",
                "filing_date": "2025-02-01",
                "complainant": "John Doe",
                "complainant_advocate": "Adv. Reddy",
                "respondent": "XYZ Ltd.",
                "respondent_advocate": "Adv. Mehta",
                "document_link": "https://e-jagriti.gov.in/.../case123"
            }
        }