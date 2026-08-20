from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ResolveRequest(BaseModel):
    address: str


class ResolveCandidate(BaseModel):
    locality_code: str
    locality_name: str
    score: float
    matched_by: str


class ResolveResponse(BaseModel):
    query: str
    candidates: List[ResolveCandidate]
    top_candidate: Optional[ResolveCandidate]
    ambiguous: bool
    confidence: float
    rationale: Dict[str, Any]
