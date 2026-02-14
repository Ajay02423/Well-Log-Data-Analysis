from pydantic import BaseModel
from typing import List, Optional, Dict, Any
class ChatResponse(BaseModel):
    answer: str
    conversation_id: Optional[str] = None


class ChatRequest(BaseModel):
    well_id: Optional[str] = None
    question: str
    selected_curves: Optional[List[str]] = []
    min_depth: Optional[float] = None
    max_depth: Optional[float] = None
    conversation_id: Optional[str] = None
