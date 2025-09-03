from fastapi import APIRouter, Depends, HTTPException, Path
from app.schemas.commission import CommissionsListResponse, CommissionResponse
from app.services.jagriti_service import JagritiService

router = APIRouter()


def get_jagriti_service() -> JagritiService:
    return JagritiService()


@router.get("/commissions/{state_id}", response_model=CommissionsListResponse)
async def get_commissions(
    state_id: str = Path(..., description="State ID"),
    service: JagritiService = Depends(get_jagriti_service)
):
    try:
        await service.initialize()
        commissions_data = await service.get_commissions(state_id)
        
        commissions = [
            CommissionResponse(
                id=comm['id'],
                name=comm['name'],
                display_name=comm['display_name'],
                state_id=comm['state_id']
            )
            for comm in commissions_data
        ]
        
        return CommissionsListResponse(
            commissions=commissions,
            total=len(commissions),
            state_id=state_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch commissions: {str(e)}"
        )