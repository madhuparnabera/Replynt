from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(default="", description="Email body content")


class AnalyzeEmailResponse(BaseModel):
    junk: bool
    priority: Optional[str] = None
    intent: Optional[str] = None
    needs_reply: Optional[bool] = None
    confidence_scores: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    models_loaded: bool
    loaded_models: List[str]

# app/models/schemas.py  — add this at the bottom

from app.models.schemas_commitment import (
    Commitment,
    CommitmentStatus,
    ExtractCommitmentsRequest,
    ExtractCommitmentsResponse,
    UpdateCommitmentRequest,
    CommitmentListResponse,
)
