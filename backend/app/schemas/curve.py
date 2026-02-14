from typing import Dict, List
from pydantic import BaseModel, Field


class DepthRangeQuery(BaseModel):
    well_id: str
    curves: List[str] = Field(..., min_items=1)
    min_depth: float
    max_depth: float


class DepthRangeResponse(BaseModel):
    depths: List[float]
    curves: Dict[str, List[float | None]]
