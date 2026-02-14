from pydantic import BaseModel
from typing import List

class InterpretRequest(BaseModel):
    well_id: str
    curves: List[str]
    min_depth: float
    max_depth: float
