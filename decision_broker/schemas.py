from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class DecisionRequest(BaseModel):
    decision_type: str
    payload: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DecisionResponse(BaseModel):
    decision: Dict[str, Any]
    confidence: float
    reason_code: str
    valid_for_seconds: int
