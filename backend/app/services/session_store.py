"""In-memory, per-process analysis sessions.

Phase 1 is intentionally stateless from a persistence standpoint (spec
section 47 privacy principle: don't store images unless necessary). Sessions
live only in server memory for a short TTL so manual corrections can
recalculate without re-uploading, then they're dropped — nothing touches
disk or a database. Phase 2 replaces this with PostgreSQL + object storage.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

import numpy as np

from app.core.config import SESSION_TTL_SECONDS
from vision.pipeline import AnalysisOutcome


@dataclass
class AnalysisSession:
    analysis_id: str
    image_bgr: np.ndarray
    outcome: AnalysisOutcome
    created_at: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self, ttl_seconds: int):
        self._sessions: dict[str, AnalysisSession] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def create(self, image_bgr: np.ndarray, outcome: AnalysisOutcome) -> AnalysisSession:
        self._evict_expired()
        analysis_id = uuid.uuid4().hex[:12]
        session = AnalysisSession(analysis_id=analysis_id, image_bgr=image_bgr, outcome=outcome)
        with self._lock:
            self._sessions[analysis_id] = session
        return session

    def get(self, analysis_id: str) -> AnalysisSession | None:
        self._evict_expired()
        with self._lock:
            return self._sessions.get(analysis_id)

    def delete(self, analysis_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(analysis_id, None) is not None

    def _evict_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [aid for aid, s in self._sessions.items() if now - s.created_at > self._ttl]
            for aid in expired:
                del self._sessions[aid]


session_store = SessionStore(ttl_seconds=SESSION_TTL_SECONDS)
