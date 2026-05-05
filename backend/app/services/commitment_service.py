"""
commitment_service.py
---------------------
Orchestrates commitment extraction and CRUD operations.
Sits between the route layer and the store / pattern utils.
"""

import logging
from typing import List, Optional

from app.models.commitment_store import store
from app.models.schemas_commitment import (
    Commitment,
    CommitmentStatus,
    ExtractCommitmentsRequest,
    ExtractCommitmentsResponse,
    UpdateCommitmentRequest,
)
from app.utils.commitment_patterns import ExtractedCommitment, extract_commitments

logger = logging.getLogger(__name__)


class CommitmentService:
    """
    All public methods return plain Pydantic models or primitives.
    No HTTP concerns live here — that belongs in the route layer.
    """

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_and_optionally_save(
        self, request: ExtractCommitmentsRequest
    ) -> ExtractCommitmentsResponse:
        """
        Run pattern extraction on the supplied email text.
        If `auto_save` is True (default), persist results to the store.
        """
        combined_text = f"{request.subject}\n\n{request.body}".strip()

        raw_extractions: List[ExtractedCommitment] = extract_commitments(
            combined_text,
            min_confidence=request.min_confidence,
        )

        logger.info(
            "Extracted %d commitment(s) from email_id=%s",
            len(raw_extractions),
            request.email_id,
        )

        commitments: List[Commitment] = []
        for ex in raw_extractions:
            c = Commitment(
                email_id=request.email_id,
                action=ex.action,
                raw_text=ex.raw_text,
                who=request.who,           # caller-supplied override
                deadline=ex.deadline,
                pattern_type=ex.pattern_type,
                confidence=ex.confidence,
            )
            if request.auto_save:
                store.add(c)
            commitments.append(c)

        return ExtractCommitmentsResponse(
            email_id=request.email_id,
            extracted_count=len(commitments),
            saved=request.auto_save,
            commitments=commitments,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_commitment(self, commitment_id: str) -> Optional[Commitment]:
        return store.get(commitment_id)

    def list_commitments(
        self,
        email_id: Optional[str] = None,
        status: Optional[CommitmentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Commitment], int]:
        """Returns (items, total_count)."""
        items = store.list(email_id=email_id, status=status, limit=limit, offset=offset)
        total = store.count(email_id=email_id, status=status)
        return items, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_commitment(
        self, commitment_id: str, request: UpdateCommitmentRequest
    ) -> Optional[Commitment]:
        """
        Partial update — only fields that are explicitly set in the request
        are written to the store. Unset fields are left unchanged.
        """
        fields = request.model_dump(exclude_unset=True)
        if not fields:
            # Nothing to update — return existing record
            return store.get(commitment_id)

        updated = store.update(commitment_id, **fields)
        if updated is None:
            logger.warning("update_commitment: id=%s not found", commitment_id)
        return updated

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_commitment(self, commitment_id: str) -> bool:
        deleted = store.delete(commitment_id)
        if not deleted:
            logger.warning("delete_commitment: id=%s not found", commitment_id)
        return deleted

    # ------------------------------------------------------------------
    # Bulk helpers
    # ------------------------------------------------------------------

    def mark_all_done_for_email(self, email_id: str) -> int:
        """Mark every pending commitment for a given email as done. Returns count updated."""
        items, _ = self.list_commitments(
            email_id=email_id, status=CommitmentStatus.PENDING, limit=1000
        )
        for item in items:
            store.update(item.id, status=CommitmentStatus.DONE)
        return len(items)


# ---------------------------------------------------------------------------
# Module-level singleton — imported by the route layer
# ---------------------------------------------------------------------------
commitment_service = CommitmentService()
