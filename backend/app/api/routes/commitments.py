"""
commitments.py  (app/api/routes/commitments.py)
-------------------------------------------------
FastAPI router for the commitment tracker.

Endpoints
---------
POST   /commitments/extract          Extract (and optionally save) commitments from email text
GET    /commitments                  List commitments with optional filters
GET    /commitments/{id}             Get a single commitment
PATCH  /commitments/{id}             Update status / deadline / notes / who
DELETE /commitments/{id}             Hard-delete a commitment
POST   /commitments/email/{email_id}/mark-done   Bulk-mark all pending for an email as done
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas_commitment import (
    Commitment,
    CommitmentListResponse,
    CommitmentStatus,
    ExtractCommitmentsRequest,
    ExtractCommitmentsResponse,
    UpdateCommitmentRequest,
)
from app.services.commitment_service import commitment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/commitments", tags=["commitments"])


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

@router.post(
    "/extract",
    response_model=ExtractCommitmentsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract commitments from email text",
    description=(
        "Runs regex pattern matching against the supplied email subject + body "
        "to detect promises, action items, and follow-up obligations. "
        "Set `auto_save=true` (default) to persist results automatically."
    ),
)
def extract_commitments(request: ExtractCommitmentsRequest) -> ExtractCommitmentsResponse:
    try:
        result = commitment_service.extract_and_optionally_save(request)
        logger.info(
            "POST /commitments/extract → %d commitment(s), email_id=%s",
            result.extracted_count,
            request.email_id,
        )
        return result
    except Exception as exc:
        logger.exception("Error during commitment extraction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=CommitmentListResponse,
    summary="List tracked commitments",
)
def list_commitments(
    email_id: Optional[str] = Query(None, description="Filter by email identifier"),
    commitment_status: Optional[CommitmentStatus] = Query(
        None,
        alias="status",
        description="Filter by status: pending | done | snoozed | dismissed",
    ),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> CommitmentListResponse:
    items, total = commitment_service.list_commitments(
        email_id=email_id,
        status=commitment_status,
        limit=limit,
        offset=offset,
    )
    return CommitmentListResponse(total=total, limit=limit, offset=offset, items=items)


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

@router.get(
    "/{commitment_id}",
    response_model=Commitment,
    summary="Get a single commitment by ID",
)
def get_commitment(commitment_id: str) -> Commitment:
    commitment = commitment_service.get_commitment(commitment_id)
    if commitment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment '{commitment_id}' not found.",
        )
    return commitment


# ---------------------------------------------------------------------------
# Update (PATCH — partial)
# ---------------------------------------------------------------------------

@router.patch(
    "/{commitment_id}",
    response_model=Commitment,
    summary="Update a commitment",
    description=(
        "Partial update. Send only the fields you want to change. "
        "Common uses: mark as done (`status: done`), snooze it "
        "(`status: snoozed`, `snoozed_until: <iso-datetime>`), "
        "or correct the deadline / who fields."
    ),
)
def update_commitment(commitment_id: str, request: UpdateCommitmentRequest) -> Commitment:
    updated = commitment_service.update_commitment(commitment_id, request)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment '{commitment_id}' not found.",
        )
    logger.info("PATCH /commitments/%s → status=%s", commitment_id, updated.status)
    return updated


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{commitment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard-delete a commitment",
)
def delete_commitment(commitment_id: str) -> None:
    deleted = commitment_service.delete_commitment(commitment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment '{commitment_id}' not found.",
        )
    logger.info("DELETE /commitments/%s", commitment_id)


# ---------------------------------------------------------------------------
# Bulk mark-done for an email
# ---------------------------------------------------------------------------

@router.post(
    "/email/{email_id}/mark-done",
    summary="Mark all pending commitments for an email as done",
)
def mark_all_done(email_id: str) -> dict:
    count = commitment_service.mark_all_done_for_email(email_id)
    return {"email_id": email_id, "marked_done": count}
