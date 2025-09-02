from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.schemas.case import CaseSearchRequest, CaseResponse, SearchType
from app.services.jagriti_service import JagritiService
from app.core.exceptions import JagritiServiceException

router = APIRouter()


def get_jagriti_service() -> JagritiService:
    service = JagritiService()
    return service


@router.post("/cases/by-case-number", response_model=List[CaseResponse])
async def search_by_case_number(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.CASE_NUMBER,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/cases/by-complainant", response_model=List[CaseResponse])
async def search_by_complainant(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.COMPLAINANT,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-respondent", response_model=List[CaseResponse])
async def search_by_respondent(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.RESPONDENT,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-complainant-advocate", response_model=List[CaseResponse])
async def search_by_complainant_advocate(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.COMPLAINANT_ADVOCATE,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-respondent-advocate", response_model=List[CaseResponse])
async def search_by_respondent_advocate(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.RESPONDENT_ADVOCATE,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-industry-type", response_model=List[CaseResponse])
async def search_by_industry_type(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.INDUSTRY_TYPE,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/by-judge", response_model=List[CaseResponse])
async def search_by_judge(
    request: CaseSearchRequest,
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        return await service.search_cases(
            SearchType.JUDGE,
            request.state,
            request.commission,
            request.search_value
        )
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))