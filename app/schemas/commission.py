from pydantic import BaseModel
from typing import List


class CommissionResponse(BaseModel):
    id: str
    name: str
    display_name: str
    state_id: str


class CommissionsListResponse(BaseModel):
    commissions: List[CommissionResponse]
    total: int
    state_id: str