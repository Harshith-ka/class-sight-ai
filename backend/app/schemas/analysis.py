from __future__ import annotations

from pydantic import BaseModel


class BBoxOut(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class SeatScoresOut(BaseModel):
    distance: float
    occlusion: float
    angle: float
    position: float
    confidence: float
    final: float
    raw_visibility: float


class SeatOut(BaseModel):
    seat_id: str
    row_index: int
    col_index: int
    bbox: BBoxOut
    occupied: bool
    detection_confidence: float
    position_category: str
    manual: bool
    scores: SeatScoresOut
    explanation: list[str]


class InstructorOut(BaseModel):
    position: list[float]
    confidence: float
    source: str
    bbox: BBoxOut | None = None


class QualityOut(BaseModel):
    resolution: str
    brightness: str
    sharpness: str
    contrast: str
    overall: int
    width: int
    height: int
    passed: bool
    reasons: list[str]


class StatsOut(BaseModel):
    seats_detected: int
    occupied: int
    empty: int
    instructor_detected: bool
    average_visibility: float
    average_obstruction: float


class ConfidenceBreakdownOut(BaseModel):
    image_quality: float
    instructor_detection: float
    seat_detection: float
    overall: float


class AnalysisResponse(BaseModel):
    analysis_id: str
    quality: QualityOut
    instructor: InstructorOut | None
    instructor_needs_manual: bool
    board_position: list[float] | None = None
    seats: list[SeatOut]
    stats: StatsOut
    heatmap_image: str | None
    overall_confidence: float
    confidence_breakdown: ConfidenceBreakdownOut
    image_width: int
    image_height: int
    detection_count: int


class SeatCorrection(BaseModel):
    occupied: bool | None = None
    delete: bool = False


class SeatCreate(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class InstructorCorrection(BaseModel):
    x: float
    y: float


class BatchImageResult(BaseModel):
    analysis_id: str
    label: str
    analysis: AnalysisResponse


class BatchSummary(BaseModel):
    image_count: int
    seats_detected_min: int
    seats_detected_max: int
    most_seats_analysis_id: str | None
    note: str


class BatchResponse(BaseModel):
    batch_id: str
    images: list[BatchImageResult]
    summary: BatchSummary
