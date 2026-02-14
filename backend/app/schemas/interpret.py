from pydantic import BaseModel
from typing import List, Dict, Any


class InterpretRequest(BaseModel):
    well_id: str
    curves: List[str]
    min_depth: float
    max_depth: float


class InterpretResponse(BaseModel):
    structured_insights: Dict[str, Any]
    interpretation_text: str
