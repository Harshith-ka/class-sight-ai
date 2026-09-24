"""Multi-photo batch analysis of the same physical classroom.

Each photo is analyzed fully independently (see batch_store.py for why —
short version: no camera calibration, so we can't honestly claim geometric
fusion). This endpoint just runs the normal pipeline per photo and groups
the results so the frontend can present them together with an honest
summary of where seat counts agree or differ across angles.
"""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.analysis import BatchResponse
from app.services.analyze_service import UploadValidationError, process_upload
from app.services.batch_store import Batch, BatchImage, batch_store
from app.services.session_store import session_store

router = APIRouter(tags=["batch"])

MIN_BATCH_IMAGES = 2
MAX_BATCH_IMAGES = 6


@router.post("/analyze/batch", response_model=BatchResponse)
async def analyze_batch(files: list[UploadFile] = File(...)) -> dict:
    if len(files) < MIN_BATCH_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Upload at least {MIN_BATCH_IMAGES} photos for a batch (use single-photo upload for one image).",
        )
    if len(files) > MAX_BATCH_IMAGES:
        raise HTTPException(status_code=400, detail=f"Upload at most {MAX_BATCH_IMAGES} photos at a time.")

    batch_images: list[BatchImage] = []
    for index, file in enumerate(files, start=1):
        raw_bytes = await file.read()
        label = file.filename or f"Photo {index}"
        try:
            session = process_upload(file.content_type, raw_bytes)
        except UploadValidationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=f"{label}: {exc.detail}") from exc
        batch_images.append(BatchImage(analysis_id=session.analysis_id, label=label))

    batch = batch_store.create(batch_images)
    return _build_batch_response(batch)


@router.get("/batch/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str) -> dict:
    batch = batch_store.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found or has expired. Please re-upload.")
    return _build_batch_response(batch)


def _build_batch_response(batch: Batch) -> dict:
    images = []
    seat_counts: list[int] = []
    for img in batch.images:
        session = session_store.get(img.analysis_id)
        if session is None:
            continue  # this photo's session expired independently; skip rather than fail the whole batch
        analysis_dict = session.outcome.to_response_dict(session.image_bgr)
        analysis_dict["analysis_id"] = session.analysis_id
        images.append({"analysis_id": session.analysis_id, "label": img.label, "analysis": analysis_dict})
        seat_counts.append(len(session.outcome.seats))

    most_seats_id = None
    if seat_counts:
        most_seats_id = images[seat_counts.index(max(seat_counts))]["analysis_id"]

    summary = {
        "image_count": len(images),
        "seats_detected_min": min(seat_counts) if seat_counts else 0,
        "seats_detected_max": max(seat_counts) if seat_counts else 0,
        "most_seats_analysis_id": most_seats_id,
        "note": (
            "Each photo was analyzed independently, not geometrically merged. Seat counts can "
            "differ by angle — a seat hidden behind a desk in one photo may be clearly visible "
            "in another — so it's worth reviewing each photo rather than trusting only the total."
        ),
    }
    return {"batch_id": batch.batch_id, "images": images, "summary": summary}
