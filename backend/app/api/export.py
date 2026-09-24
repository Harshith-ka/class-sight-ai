from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.export import export_training_sample
from app.services.session_store import session_store

router = APIRouter(tags=["export"])


@router.post("/analyze/{analysis_id}/export")
async def export_analysis(analysis_id: str) -> dict:
    session = session_store.get(analysis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Analysis not found or has expired. Please re-upload.")
    if not session.outcome.seats:
        raise HTTPException(status_code=422, detail="No seats to export — nothing was detected or added.")
    return export_training_sample(session)
