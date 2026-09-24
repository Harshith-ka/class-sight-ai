"""Groups several analyses of the same physical classroom together.

This is intentionally *not* geometric multi-view fusion (spec section 59's
"combine into a more reliable classroom representation" / "multi-view
confidence: 96%"). Each photo is analyzed fully independently — there's no
camera calibration or registration between shots, so we cannot honestly
merge seat positions into one shared coordinate system. What we can do
honestly: run each photo through the normal pipeline, group the results,
and summarize where they agree/disagree (e.g. a seat hidden behind a desk
in one angle might be clearly visible in another).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

from app.core.config import SESSION_TTL_SECONDS


@dataclass
class BatchImage:
    analysis_id: str
    label: str


@dataclass
class Batch:
    batch_id: str
    images: list[BatchImage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class BatchStore:
    def __init__(self, ttl_seconds: int):
        self._batches: dict[str, Batch] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def create(self, images: list[BatchImage]) -> Batch:
        self._evict_expired()
        batch = Batch(batch_id=uuid.uuid4().hex[:12], images=images)
        with self._lock:
            self._batches[batch.batch_id] = batch
        return batch

    def get(self, batch_id: str) -> Batch | None:
        self._evict_expired()
        with self._lock:
            return self._batches.get(batch_id)

    def _evict_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [bid for bid, b in self._batches.items() if now - b.created_at > self._ttl]
            for bid in expired:
                del self._batches[bid]


batch_store = BatchStore(ttl_seconds=SESSION_TTL_SECONDS)
