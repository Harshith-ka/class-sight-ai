"""Manual correction mutations (spec section 29).

Each function mutates an AnalysisOutcome in place; the API layer is
responsible for calling `vision.pipeline.recalculate` afterward so scores
reflect the correction.
"""
from __future__ import annotations

from collections.abc import Iterable

from vision.models import BBox, Instructor, Seat
from vision.pipeline import AnalysisOutcome
from vision.seats.row_clustering import build_seats


def move_instructor(outcome: AnalysisOutcome, x: float, y: float) -> None:
    outcome.instructor = Instructor(position=(x, y), confidence=1.0, bbox=None, source="manual")


def move_board(outcome: AnalysisOutcome, x: float, y: float) -> None:
    """Marking the board gives the visibility engine a real "facing toward"
    reference instead of assuming bottom-center of the frame — improves
    angle scoring, not just cosmetic (see visibility_engine.py)."""
    outcome.board_position = (x, y)


def move_seat(outcome: AnalysisOutcome, seat_id: str, x: float, y: float) -> bool:
    """Shift an existing seat's bbox so its center lands on (x, y), keeping
    its size and occupied status. Covers "correct classroom rows" (spec
    section 29) — moving a seat into the right row/column re-triggers the
    same clustering/relabeling used everywhere else, rather than needing a
    separate dedicated row-editing tool."""
    for seat in outcome.seats:
        if seat.seat_id != seat_id:
            continue
        half_w = seat.bbox.width / 2
        half_h = seat.bbox.height / 2
        cx = min(max(x, half_w), 1.0 - half_w)
        cy = min(max(y, half_h), 1.0 - half_h)
        new_bbox = BBox(cx - half_w, cy - half_h, cx + half_w, cy + half_h)

        candidates = [
            ((new_bbox if s.seat_id == seat_id else s.bbox), s.occupied, s.detection_confidence)
            for s in outcome.seats
        ]
        outcome.seats = _relabel_from_candidates(outcome.seats, candidates, extra_manual_bbox=new_bbox)
        return True
    return False


def update_seat_occupancy(outcome: AnalysisOutcome, seat_id: str, occupied: bool | None) -> bool:
    for seat in outcome.seats:
        if seat.seat_id == seat_id:
            if occupied is not None:
                seat.occupied = occupied
            seat.manual = True
            return True
    return False


def delete_seat(outcome: AnalysisOutcome, seat_id: str) -> bool:
    remaining = [s for s in outcome.seats if s.seat_id != seat_id]
    if len(remaining) == len(outcome.seats):
        return False
    outcome.seats = _relabel(remaining)
    return True


def add_seat(outcome: AnalysisOutcome, x1: float, y1: float, x2: float, y2: float) -> Seat:
    new_bbox = BBox(x1, y1, x2, y2)
    candidates = [(s.bbox, s.occupied, s.detection_confidence) for s in outcome.seats]
    candidates.append((new_bbox, False, 1.0))
    outcome.seats = _relabel_from_candidates(outcome.seats, candidates, extra_manual_bbox=new_bbox)
    return next(s for s in outcome.seats if s.bbox == new_bbox)


def _relabel(seats: Iterable[Seat]) -> list[Seat]:
    seats = list(seats)
    candidates = [(s.bbox, s.occupied, s.detection_confidence) for s in seats]
    return _relabel_from_candidates(seats, candidates)


def _relabel_from_candidates(
    original_seats: Iterable[Seat], candidates: list[tuple[BBox, bool, float]], extra_manual_bbox: BBox | None = None
) -> list[Seat]:
    manual_bboxes = {s.bbox for s in original_seats if s.manual}
    if extra_manual_bbox is not None:
        manual_bboxes.add(extra_manual_bbox)
    rebuilt = build_seats(candidates)
    for seat in rebuilt:
        if seat.bbox in manual_bboxes:
            seat.manual = True
    return rebuilt
