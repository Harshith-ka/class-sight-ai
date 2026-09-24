"""End-to-end analysis pipeline (spec section 55): quality check -> detect ->
seats -> instructor -> visibility scoring -> heatmap -> serialized result.

This is the single entry point the FastAPI backend calls. Kept free of any
web-framework or storage concerns so it stays independently testable and
reusable.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from vision.detection.detector import ObjectDetector
from vision.detection.quality import assess_quality
from vision.geometry.vectors import clamp
from vision.models import Detection, Instructor, Seat
from vision.seats.row_clustering import build_seats
from vision.seats.seat_detector import detect_candidate_seats
from vision.visibility.heatmap import generate_heatmap
from vision.visibility.instructor import LOW_CONFIDENCE_THRESHOLD, detect_instructor
from vision.visibility.scorer import score_seats


class AnalysisError(Exception):
    """Raised when the image fails the pre-inference quality gate."""


_detector_singleton: ObjectDetector | None = None


def get_detector() -> ObjectDetector:
    global _detector_singleton
    if _detector_singleton is None:
        _detector_singleton = ObjectDetector()
    return _detector_singleton


@dataclass
class AnalysisOutcome:
    """Holds the intermediate pipeline state a backend session needs to keep
    around so manual corrections (spec section 29) can recompute scores
    without re-running detection."""

    quality_dict: dict
    detections: list[Detection]
    seats: list[Seat]
    instructor: Instructor | None
    board_position: tuple[float, float] | None = None

    def to_response_dict(self, image_bgr: np.ndarray) -> dict:
        heatmap_b64 = generate_heatmap(image_bgr, self.seats, self.instructor) if self.seats else None
        return serialize_result(
            detections=self.detections,
            seats=self.seats,
            instructor=self.instructor,
            quality_dict=self.quality_dict,
            heatmap_b64=heatmap_b64,
            image_width=image_bgr.shape[1],
            image_height=image_bgr.shape[0],
            board_position=self.board_position,
        )


def analyze(image_bgr: np.ndarray) -> AnalysisOutcome:
    quality = assess_quality(image_bgr)
    if not quality.passed:
        raise AnalysisError(
            "The classroom structure cannot be reliably detected. "
            "Try uploading a wider or clearer image."
        )

    detections = get_detector().detect(image_bgr)
    seats = build_seats(detect_candidate_seats(detections))
    instructor = detect_instructor(detections)

    if instructor is not None and seats:
        score_seats(seats, instructor, detections)

    return AnalysisOutcome(
        quality_dict=quality.to_dict(), detections=detections, seats=seats, instructor=instructor
    )


def recalculate(outcome: AnalysisOutcome, image_bgr: np.ndarray) -> dict:
    """Re-run visibility scoring after a manual correction (spec section 29/section 39
    `corrections` table) and return a fresh response dict."""
    if outcome.instructor is not None and outcome.seats:
        score_seats(outcome.seats, outcome.instructor, outcome.detections, forward_target=outcome.board_position)
    return outcome.to_response_dict(image_bgr)


def run_analysis(image_bgr: np.ndarray) -> dict:
    return analyze(image_bgr).to_response_dict(image_bgr)


def serialize_result(
    *,
    detections: list[Detection],
    seats: list[Seat],
    instructor: Instructor | None,
    quality_dict: dict,
    heatmap_b64: str | None,
    image_width: int,
    image_height: int,
    board_position: tuple[float, float] | None = None,
) -> dict:
    stats = compute_stats(seats, instructor)
    breakdown = confidence_breakdown(quality_dict, instructor, seats)
    return {
        "quality": quality_dict,
        "instructor": instructor_to_dict(instructor),
        "instructor_needs_manual": instructor is None or instructor.confidence < LOW_CONFIDENCE_THRESHOLD,
        "board_position": list(board_position) if board_position else None,
        "seats": [seat_to_dict(s) for s in seats],
        "stats": stats,
        "heatmap_image": heatmap_b64,
        "overall_confidence": breakdown["overall"],
        "confidence_breakdown": breakdown,
        "image_width": image_width,
        "image_height": image_height,
        "detection_count": len(detections),
    }


def compute_stats(seats: list[Seat], instructor: Instructor | None) -> dict:
    occupied = sum(1 for s in seats if s.occupied)
    avg_visibility = sum(s.scores.raw_visibility for s in seats) / len(seats) if seats else 0.0
    avg_obstruction = sum(s.scores.occlusion for s in seats) / len(seats) if seats else 0.0
    return {
        "seats_detected": len(seats),
        "occupied": occupied,
        "empty": len(seats) - occupied,
        "instructor_detected": instructor is not None,
        "average_visibility": round(avg_visibility, 1),
        "average_obstruction": round(avg_obstruction, 1),
    }


def confidence_breakdown(quality_dict: dict, instructor: Instructor | None, seats: list[Seat]) -> dict:
    """Only genuinely-computed components — no fabricated 'Student Detection'
    or 'Classroom Mapping' numbers we have no real independent signal for
    (spec section 68: don't overstate certainty)."""
    quality_component = quality_dict["overall"] / 100
    instructor_component = instructor.confidence if instructor else 0.2
    seat_component = sum(s.detection_confidence for s in seats) / len(seats) if seats else 0.3
    overall = clamp((0.3 * quality_component + 0.35 * instructor_component + 0.35 * seat_component) * 100)
    return {
        "image_quality": round(quality_component * 100, 1),
        "instructor_detection": round(instructor_component * 100, 1),
        "seat_detection": round(seat_component * 100, 1),
        "overall": round(overall, 1),
    }


def instructor_to_dict(instructor: Instructor | None) -> dict | None:
    if instructor is None:
        return None
    return {
        "position": list(instructor.position),
        "confidence": round(instructor.confidence, 3),
        "source": instructor.source,
        "bbox": _bbox_to_dict(instructor.bbox) if instructor.bbox else None,
    }


def seat_to_dict(seat: Seat) -> dict:
    return {
        "seat_id": seat.seat_id,
        "row_index": seat.row_index,
        "col_index": seat.col_index,
        "bbox": _bbox_to_dict(seat.bbox),
        "occupied": seat.occupied,
        "detection_confidence": round(seat.detection_confidence, 3),
        "position_category": seat.position_category,
        "manual": seat.manual,
        "scores": {
            "distance": seat.scores.distance,
            "occlusion": seat.scores.occlusion,
            "angle": seat.scores.angle,
            "position": seat.scores.position,
            "confidence": seat.scores.confidence,
            "final": seat.scores.final,
            "raw_visibility": seat.scores.raw_visibility,
        },
        "explanation": seat.explanation,
    }


def _bbox_to_dict(bbox) -> dict:
    return {"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2}
