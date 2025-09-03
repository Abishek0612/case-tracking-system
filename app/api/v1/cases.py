from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.schemas.case import CaseSearchRequest, CaseResponse, CaseSearchResponse, SearchType
from app.services.jagriti_service import JagritiService
from app.core.exceptions import (
    JagritiServiceException, StateNotFoundException, 
    CommissionNotFoundException, CaptchaRequiredException,
    SearchTimeoutException
)

router = APIRouter()


async def get_jagriti_service() -> JagritiService:
    service = JagritiService()
    await service.initialize()
    return service


@router.post("/cases/by-case-number", response_model=List[CaseResponse])
async def search_by_case_number(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by case number"""
    try:
        return await service.search_cases(
            SearchType.CASE_NUMBER,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/cases/by-complainant", response_model=List[CaseResponse])
async def search_by_complainant(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by complainant name"""
    try:
        return await service.search_cases(
            SearchType.COMPLAINANT,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-respondent", response_model=List[CaseResponse])
async def search_by_respondent(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by respondent name"""
    try:
        return await service.search_cases(
            SearchType.RESPONDENT,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-complainant-advocate", response_model=List[CaseResponse])
async def search_by_complainant_advocate(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by complainant advocate name"""
    try:
        return await service.search_cases(
            SearchType.COMPLAINANT_ADVOCATE,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-respondent-advocate", response_model=List[CaseResponse])
async def search_by_respondent_advocate(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by respondent advocate name"""
    try:
        return await service.search_cases(
            SearchType.RESPONDENT_ADVOCATE,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-industry-type", response_model=List[CaseResponse])
async def search_by_industry_type(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by industry type"""
    try:
        return await service.search_cases(
            SearchType.INDUSTRY_TYPE,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-judge", response_model=List[CaseResponse])
async def search_by_judge(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Search cases by judge name"""
    try:
        return await service.search_cases(
            SearchType.JUDGE,
            request.state,
            request.commission,
            request.search_value,
            case_type=request.case_type.value,
            date_filter=request.date_filter.value,
            from_date=request.from_date,
            to_date=request.to_date
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/advanced-search", response_model=CaseSearchResponse)
async def advanced_search(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    """Advanced case search with pagination and full response"""
    try:
        return await service.advanced_search_cases(request)
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CaptchaRequiredException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except SearchTimeoutException as e:
        raise HTTPException(status_code=408, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cases/health")
async def cases_health_check():
    """Health check endpoint for cases service"""
    return {"status": "healthy", "service": "cases", "timestamp": datetime.now().isoformat()}