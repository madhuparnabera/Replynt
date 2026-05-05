"""
schemas_commitment.py
---------------------
Pydantic schemas for the commitment tracker.

Paste these classes into your existing app/models/schemas.py,
or import them from here and re-export from schemas.py.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CommitmentStatus(str, Enum):
    PENDING  = "pending"
    DONE     = "done"
    SNOOZED  = "snoozed"
    DISMISSED = "dismissed"


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

class Commitment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Where did this commitment come from?
    email_id: Optional[str] = Field(
        None,
        description="Caller-supplied email identifier (message-id, thread-id, etc.)"
    )

    # What was promised?
    action: str = Field(..., description="The commitment / promise extracted from the email")
    raw_text: str = Field(..., description="The original sentence the commitment was extracted from")

    # Who is involved?
    who: Optional[str] = Field(
        None,
        description="Person responsible for the commitment (inferred or supplied by caller)"
    )

    # When?
    deadline: Optional[str] = Field(
        None,
        description="Deadline string as extracted from the email (e.g. 'Friday', 'end of day')"
    )

    # Metadata
    status: CommitmentStatus = CommitmentStatus.PENDING
    pattern_type: str = Field("unknown", description="Which extraction pattern matched")
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snoozed_until: Optional[datetime] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Request / response bodies
# ---------------------------------------------------------------------------

class ExtractCommitmentsRequest(BaseModel):
    """
    Body for POST /commitments/extract
    Submit raw email text; get back extracted commitments.
    """
    email_id: Optional[str] = Field(None, description="Your identifier for the email")
    subject: str = Field("", description="Email subject line")
    body: str = Field(..., description="Email body text")
    who: Optional[str] = Field(None, description="Override the 'who' field for all extracted commitments")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Drop extractions below this confidence")
    auto_save: bool = Field(
        True,
        description="If true, extracted commitments are saved to the store automatically"
    )


class UpdateCommitmentRequest(BaseModel):
    """Body for PATCH /commitments/{id}"""
    status: Optional[CommitmentStatus] = None
    deadline: Optional[str] = None
    who: Optional[str] = None
    notes: Optional[str] = None
    snoozed_until: Optional[datetime] = None


class CommitmentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Commitment]


class ExtractCommitmentsResponse(BaseModel):
    email_id: Optional[str]
    extracted_count: int
    saved: bool
    commitments: List[Commitment]
