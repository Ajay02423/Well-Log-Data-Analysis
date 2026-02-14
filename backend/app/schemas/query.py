from pydantic import BaseModel
from typing import List, Dict


class DepthRangeRequest(BaseModel):
    well_id: str
    curves: List[str]
    min_depth: float
    max_depth: float


class DepthRangeResponse(BaseModel):
    depths: List[float]
    curves: Dict[str, List[float | None]]

class DepthRangeInfo(BaseModel):
    min_depth: float
    max_depth: float
