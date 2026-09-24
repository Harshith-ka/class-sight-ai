"""Weighted seat scoring and explanations (spec sections 22 & 61).

Final Score = 25% Distance + 30% Occlusion + 20% Angle + 15% Position + 10% Confidence

Higher score = lower estimated exposure to the instructor (spec section 22's
0=high concern / 100=low concern scale). The UI must label this
"Visibility / Exposure Score" and never claim certainty (spec section 68) —
that framing lives in the frontend copy, not here.
"""
from __future__ import annotations

from vision.geometry.vectors import clamp
from vision.models import Detection, Instructor, Seat, SeatScores
from vision.visibility.visibility_engine import DEFAULT_FORWARD_TARGET, compute_seat_geometry

WEIGHTS = {"distance": 0.25, "occlusion": 0.30, "angle": 0.20, "position": 0.15, "confidence": 0.10}

POSITION_SCORES = {
    "front-center": 15, "front-side": 30, "front-corner": 40,
    "middle-center": 45, "middle-side": 55, "middle-corner": 65,
    "rear-center": 70, "rear-side": 82, "rear-corner": 90,
}

MAX_DISTANCE = 1.2  # ~diagonal of the normalized frame; caps the distance score at 100
MAX_ANGLE_DEG = 75.0


def score_seats(
    seats: list[Seat],
    instructor: Instructor,
    detections: list[Detection],
    forward_target: tuple[float, float] | None = None,
) -> None:
    if not seats:
        return

    target = forward_target if forward_target is not None else DEFAULT_FORWARD_TARGET

    row_counts: dict[int, int] = {}
    for seat in seats:
        row_counts[seat.row_index] = row_counts.get(seat.row_index, 0) + 1
    total_rows = max(seat.row_index for seat in seats) + 1

    for seat in seats:
        raw_distance, raw_angle_deg, occlusion, position_category = compute_seat_geometry(
            seat, instructor, detections, total_rows, row_counts[seat.row_index], forward_target=target
        )

        distance_score = clamp(raw_distance / MAX_DISTANCE * 100)
        occlusion_score = clamp(occlusion * 100)
        angle_score = clamp(raw_angle_deg / MAX_ANGLE_DEG * 100)
        position_score = POSITION_SCORES.get(position_category, 50)
        confidence_score = clamp(seat.detection_confidence * 100)

        final = (
            WEIGHTS["distance"] * distance_score
            + WEIGHTS["occlusion"] * occlusion_score
            + WEIGHTS["angle"] * angle_score
            + WEIGHTS["position"] * position_score
            + WEIGHTS["confidence"] * confidence_score
        )

        seat.position_category = position_category
        seat.scores = SeatScores(
            distance=round(distance_score, 1),
            occlusion=round(occlusion_score, 1),
            angle=round(angle_score, 1),
            position=round(float(position_score), 1),
            confidence=round(confidence_score, 1),
            final=round(clamp(final), 1),
            raw_distance=round(raw_distance, 4),
            raw_visibility=round(clamp(100 - occlusion_score), 1),
            raw_angle_deg=round(raw_angle_deg, 1),
        )
        seat.explanation = _explain(seat)


def _explain(seat: Seat) -> list[str]:
    s = seat.scores
    reasons: list[str] = []

    if s.occlusion >= 55:
        reasons.append("Significant visual obstruction detected between the instructor and this seat.")
    elif s.occlusion <= 20:
        reasons.append("Estimated clear line of sight from the instructor to this seat.")

    if s.distance >= 60:
        reasons.append("Large estimated distance from the instructor.")
    elif s.distance <= 30:
        reasons.append("Close to the instructor's estimated position.")

    if s.angle >= 55:
        reasons.append("Off-center viewing angle relative to the instructor's typical line of sight.")
    else:
        reasons.append("Near the instructor's direct line of sight.")

    reasons.append(f"Seat position estimated as {seat.position_category.replace('-', ' ')}.")
    reasons.append(
        "Detection confidence for this seat is high."
        if s.confidence >= 70
        else "Detection confidence for this seat is lower than average."
    )
    return reasons
