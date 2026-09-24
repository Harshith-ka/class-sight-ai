"""Heuristic instructor detection (spec section 16, Signals 2 & 3).

No `teacher` class is available without custom training (Phase 3), so the
instructor is inferred from position alone: the person nearest the top of
the frame and closest to horizontal center scores highest, since classroom
photos are typically taken from the back of the room looking toward the
board/front.

Confidence reflects both the raw detection confidence and how much the
winning candidate's score beats the runner-up — a photo with two people
near the front produces a lower-confidence guess and should prompt manual
selection in the UI (spec section 29).
"""
from __future__ import annotations

from vision.models import Detection, Instructor

TOP_WEIGHT = 0.6
CENTER_WEIGHT = 0.4
LOW_CONFIDENCE_THRESHOLD = 0.4


def detect_instructor(detections: list[Detection]) -> Instructor | None:
    persons = [d for d in detections if d.class_name == "person"]
    if not persons:
        return None

    scored = []
    for person in persons:
        topness = 1 - person.bbox.cy
        centeredness = max(0.0, 1 - 2 * abs(person.bbox.cx - 0.5))
        position_score = TOP_WEIGHT * topness + CENTER_WEIGHT * centeredness
        scored.append((position_score, person))
    scored.sort(key=lambda item: item[0], reverse=True)

    best_score, best = scored[0]
    margin = (best_score - scored[1][0]) if len(scored) > 1 else 1.0
    confidence = max(0.05, min(0.99, (0.5 + margin * 1.5) * best.confidence))

    # Feet position (bottom-center of bbox) approximates where the person stands.
    position = (best.bbox.cx, best.bbox.y2)
    return Instructor(position=position, confidence=confidence, bbox=best.bbox, source="heuristic")
