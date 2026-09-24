from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisResponse, InstructorCorrection, SeatCorrection, SeatCreate
from app.services import corrections
from app.services.session_store import AnalysisSession, session_store
from vision.pipeline import recalculate

router = APIRouter(tags=["corrections"])


def _get_session(analysis_id: str) -> AnalysisSession:
    session = session_store.get(analysis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Analysis not found or has expired. Please re-upload.")
    return session


def _respond(session: AnalysisSession) -> dict:
    result = recalculate(session.outcome, session.image_bgr)
    result["analysis_id"] = session.analysis_id
    return result


@router.patch("/analyze/{analysis_id}/instructor", response_model=AnalysisResponse)
async def correct_instructor(analysis_id: str, body: InstructorCorrection) -> dict:
    session = _get_session(analysis_id)
    corrections.move_instructor(session.outcome, body.x, body.y)
    return _respond(session)


@router.patch("/analyze/{analysis_id}/board", response_model=AnalysisResponse)
async def correct_board(analysis_id: str, body: InstructorCorrection) -> dict:
    session = _get_session(analysis_id)
    corrections.move_board(session.outcome, body.x, body.y)
    return _respond(session)


@router.patch("/analyze/{analysis_id}/seats/{seat_id}/move", response_model=AnalysisResponse)
async def move_seat(analysis_id: str, seat_id: str, body: InstructorCorrection) -> dict:
    session = _get_session(analysis_id)
    found = corrections.move_seat(session.outcome, seat_id, body.x, body.y)
    if not found:
        raise HTTPException(status_code=404, detail=f"Seat '{seat_id}' not found in this analysis.")
    return _respond(session)


@router.patch("/analyze/{analysis_id}/seats/{seat_id}", response_model=AnalysisResponse)
async def correct_seat(analysis_id: str, seat_id: str, body: SeatCorrection) -> dict:
    session = _get_session(analysis_id)
    if body.delete:
        found = corrections.delete_seat(session.outcome, seat_id)
    else:
        found = corrections.update_seat_occupancy(session.outcome, seat_id, body.occupied)
    if not found:
        raise HTTPException(status_code=404, detail=f"Seat '{seat_id}' not found in this analysis.")
    return _respond(session)


@router.post("/analyze/{analysis_id}/seats", response_model=AnalysisResponse)
async def create_seat(analysis_id: str, body: SeatCreate) -> dict:
    session = _get_session(analysis_id)
    corrections.add_seat(session.outcome, body.x1, body.y1, body.x2, body.y2)
    return _respond(session)


@router.post("/analyze/{analysis_id}/recalculate", response_model=AnalysisResponse)
async def force_recalculate(analysis_id: str) -> dict:
    session = _get_session(analysis_id)
    return _respond(session)
