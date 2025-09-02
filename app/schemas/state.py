from pydantic import BaseModel
from typing import List


class StateResponse(BaseModel):
    id: str
    name: str
    display_name: str


class StatesListResponse(BaseModel):
    states: List[StateResponse]
    total: int