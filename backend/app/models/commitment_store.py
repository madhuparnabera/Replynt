"""
commitment_store.py
-------------------
Thread-safe in-memory store for commitments.

Designed so it can be swapped out for a SQLAlchemy / SQLite / Postgres
store later with zero changes to the service or route layers — just replace
the module-level `store` instance.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.schemas import Commitment, CommitmentStatus


class InMemoryCommitmentStore:
    """
    Simple dict-backed store protected by a reentrant lock.
    Suitable for single-process deployments and prototyping.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Commitment] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(self, commitment: Commitment) -> Commitment:
        with self._lock:
            self._data[commitment.id] = commitment
        return commitment

    def update(self, commitment_id: str, **fields) -> Optional[Commitment]:
        with self._lock:
            existing = self._data.get(commitment_id)
            if existing is None:
                return None
            updated_data = existing.model_dump()
            updated_data.update(fields)
            updated_data["updated_at"] = datetime.now(timezone.utc)
            updated = Commitment(**updated_data)
            self._data[commitment_id] = updated
            return updated

    def delete(self, commitment_id: str) -> bool:
        with self._lock:
            if commitment_id in self._data:
                del self._data[commitment_id]
                return True
            return False

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, commitment_id: str) -> Optional[Commitment]:
        with self._lock:
            return self._data.get(commitment_id)

    def list(
        self,
        email_id: Optional[str] = None,
        status: Optional[CommitmentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Commitment]:
        with self._lock:
            items = list(self._data.values())

        if email_id:
            items = [c for c in items if c.email_id == email_id]
        if status:
            items = [c for c in items if c.status == status]

        # Newest first
        items.sort(key=lambda c: c.created_at, reverse=True)
        return items[offset : offset + limit]

    def count(
        self,
        email_id: Optional[str] = None,
        status: Optional[CommitmentStatus] = None,
    ) -> int:
        return len(self.list(email_id=email_id, status=status, limit=10_000))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Wipe all data — useful in tests."""
        with self._lock:
            self._data.clear()


# ---------------------------------------------------------------------------
# Module-level singleton — imported by commitment_service and routes
# ---------------------------------------------------------------------------
store = InMemoryCommitmentStore()
