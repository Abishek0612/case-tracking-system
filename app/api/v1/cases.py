from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.schemas.case import CaseSearchRequest, CaseResponse, SearchType
from app.services.jagriti_service import JagritiService
from app.core.exceptions import StateNotFoundException, CommissionNotFoundException, JagritiServiceException

router = APIRouter()


async def get_jagriti_service() -> JagritiService:
    service = JagritiService()
    await service.initialize()
    return service


async def handle_search(
    request: CaseSearchRequest,
    search_type: SearchType,
    service: JagritiService
) -> List[CaseResponse]:
    try:
        return await service.search_cases(
            search_type,
            request.state,
            request.commission,
            request.search_value
        )
    except StateNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommissionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except JagritiServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/cases/by-case-number", response_model=List[CaseResponse])
async def search_by_case_number(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.CASE_NUMBER, service)


@router.post("/cases/by-complainant", response_model=List[CaseResponse])
async def search_by_complainant(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.COMPLAINANT, service)


@router.post("/cases/by-respondent", response_model=List[CaseResponse])
async def search_by_respondent(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.RESPONDENT, service)


@router.post("/cases/by-complainant-advocate", response_model=List[CaseResponse])
async def search_by_complainant_advocate(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.COMPLAINANT_ADVOCATE, service)


@router.post("/cases/by-respondent-advocate", response_model=List[CaseResponse])
async def search_by_respondent_advocate(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.RESPONDENT_ADVOCATE, service)


@router.post("/cases/by-industry-type", response_model=List[CaseResponse])
async def search_by_industry_type(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.INDUSTRY_TYPE, service)


@router.post("/cases/by-judge", response_model=List[CaseResponse])
async def search_by_judge(request: CaseSearchRequest):
    service = await get_jagriti_service()
    return await handle_search(request, SearchType.JUDGE, service)


@router.get("/cases/health")
async def cases_health_check():
    return {"status": "healthy", "service": "cases", "timestamp": datetime.now().isoformat()}