"""Shared upload -> analysis pipeline, used by both the single-image and
batch endpoints so validation/error behavior stays identical either way."""
from __future__ import annotations

from app.core.config import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_BYTES
from app.services.image_io import decode_image
from app.services.session_store import AnalysisSession, session_store
from vision.pipeline import AnalysisError, analyze


class UploadValidationError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def process_upload(content_type: str | None, raw_bytes: bytes) -> AnalysisSession:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError(415, "Unsupported file type. Upload JPG, PNG, or WEBP.")
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise UploadValidationError(413, "File too large. Maximum size is 10 MB.")

    try:
        image_bgr = decode_image(raw_bytes)
    except ValueError as exc:
        raise UploadValidationError(400, str(exc)) from exc

    try:
        outcome = analyze(image_bgr)
    except AnalysisError as exc:
        raise UploadValidationError(422, str(exc)) from exc

    return session_store.create(image_bgr, outcome)
