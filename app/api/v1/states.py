from fastapi import APIRouter, Depends, HTTPException
from app.schemas.state import StatesListResponse, StateResponse
from app.services.jagriti_service import JagritiService

router = APIRouter()


def get_jagriti_service() -> JagritiService:
    return JagritiService()


@router.get("/states", response_model=StatesListResponse)
async def get_states(service: JagritiService = Depends(get_jagriti_service)):
    try:
        await service.initialize()
        states_data = await service.get_states()
        
        states = [
            StateResponse(
                id=state['id'],
                name=state['name'],
                display_name=state['display_name']
            )
            for state in states_data
        ]
        
        return StatesListResponse(states=states, total=len(states))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch states: {str(e)}")