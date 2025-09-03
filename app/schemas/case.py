from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
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


class CaseType(str, Enum):
    DAILY_ORDER = "Daily Order"
    JUDGMENT = "Judgment"
    ALL = "All"


class DateFilter(str, Enum):
    FILING_DATE = "case_filing_date"
    HEARING_DATE = "hearing_date"
    ORDER_DATE = "order_date"


class CaseSearchRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., KARNATAKA)", min_length=2)
    commission: str = Field(..., description="Commission name", min_length=3)
    search_value: str = Field(..., min_length=1, description="Search value")
    case_type: CaseType = Field(default=CaseType.DAILY_ORDER, description="Type of case to search")
    date_filter: DateFilter = Field(default=DateFilter.FILING_DATE, description="Date filter type")
    from_date: Optional[str] = Field(None, description="Start date (DD/MM/YYYY)")
    to_date: Optional[str] = Field(None, description="End date (DD/MM/YYYY)")
    page: int = Field(default=1, ge=1, le=100, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Results per page")
    
    @validator('state', 'commission', 'search_value')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('from_date', 'to_date')
    def validate_date_format(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', v):
            raise ValueError('Date must be in DD/MM/YYYY format')
        try:
            datetime.strptime(v, '%d/%m/%Y')
        except ValueError:
            raise ValueError('Invalid date')
        return v
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if v is None or values.get('from_date') is None:
            return v
        from_dt = datetime.strptime(values['from_date'], '%d/%m/%Y')
        to_dt = datetime.strptime(v, '%d/%m/%Y')
        if to_dt < from_dt:
            raise ValueError('to_date must be after from_date')
        return v


class CaseStatus(str, Enum):
    PENDING = "Pending"
    HEARING = "Hearing"
    DISPOSED = "Disposed"
    DISMISSED = "Dismissed"
    SETTLED = "Settled"
    WITHDRAWN = "Withdrawn"


class CaseResponse(BaseModel):
    case_number: str
    case_stage: str
    filing_date: str
    complainant: str
    complainant_advocate: Optional[str] = None
    respondent: str
    respondent_advocate: Optional[str] = None
    document_link: Optional[str] = None
    case_type: Optional[str] = None
    next_hearing_date: Optional[str] = None
    court_fee: Optional[str] = None
    case_value: Optional[str] = None
    
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
                "document_link": "https://e-jagriti.gov.in/case/123",
                "case_type": "Consumer Complaint",
                "next_hearing_date": "2025-03-15",
                "court_fee": "₹500",
                "case_value": "₹50,000"
            }
        }


class CaseSearchResponse(BaseModel):
    cases: List[CaseResponse]
    total_found: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool
    search_params: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "cases": [],
                "total_found": 150,
                "page": 1,
                "limit": 50,
                "total_pages": 3,
                "has_next": True,
                "has_previous": False,
                "search_params": {
                    "search_type": "complainant",
                    "state": "KARNATAKA",
                    "commission": "Bangalore Urban",
                    "search_value": "Reddy"
                }
            }
        }