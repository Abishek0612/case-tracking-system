from fastapi import APIRouter, HTTPException
from app.schemas.state import StatesListResponse, StateResponse
from app.services.jagriti_service import JagritiService

router = APIRouter()


@router.get("/states", response_model=StatesListResponse)
async def get_states():
    try:
        service = JagritiService()
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