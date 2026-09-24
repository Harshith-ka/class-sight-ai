from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.analysis import AnalysisResponse
from app.services.analyze_service import UploadValidationError, process_upload
from app.services.session_store import session_store

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)) -> dict:
    raw_bytes = await file.read()
    try:
        session = process_upload(file.content_type, raw_bytes)
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    result = session.outcome.to_response_dict(session.image_bgr)
    result["analysis_id"] = session.analysis_id
    return result


@router.get("/analyze/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str) -> dict:
    session = session_store.get(analysis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Analysis not found or has expired. Please re-upload.")
    result = session.outcome.to_response_dict(session.image_bgr)
    result["analysis_id"] = session.analysis_id
    return result


@router.delete("/analyze/{analysis_id}")
async def delete_analysis(analysis_id: str) -> dict:
    deleted = session_store.delete(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found or has already expired.")
    return {"deleted": True}
