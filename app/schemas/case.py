from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class SearchType(str, Enum):
    CASE_NUMBER = "case_number"
    COMPLAINANT = "complainant"
    RESPONDENT = "respondent"
    COMPLAINANT_ADVOCATE = "complainant_advocate"
    RESPONDENT_ADVOCATE = "respondent_advocate"
    INDUSTRY_TYPE = "industry_type"
    JUDGE = "judge"


class CaseSearchRequest(BaseModel):
    state: str = Field(..., description="State name", min_length=2)
    commission: str = Field(..., description="Commission name", min_length=3)
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
                "case_number": "DC/123/2025",
                "case_stage": "Hearing",
                "filing_date": "2025-01-15",
                "complainant": "John Doe",
                "complainant_advocate": "Adv. Reddy",
                "respondent": "XYZ Ltd.",
                "respondent_advocate": "Adv. Mehta",
                "document_link": "https://e-jagriti.gov.in/case/123"
            }
        }