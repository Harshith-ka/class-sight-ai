"""Cluster candidate seats into rows and assign human-readable labels.

Uses a gap-based 1D clustering on the vertical (y) center of each seat
(spec section 19) rather than a fixed row count, since classrooms vary in
layout. Within a row, seats are ordered left-to-right and numbered.
"""
from __future__ import annotations

from vision.models import Seat
from vision.seats.seat_detector import CandidateSeat

MIN_ROW_GAP = 0.05
ROW_GAP_FACTOR = 1.6
# Below this many gaps, "median gap" is too self-referential to trust (with
# exactly one gap, it *is* the gap, so `gap > median*factor` can never be
# true and two seats can never split into two rows no matter how far apart
# they are). Fall back to the fixed MIN_ROW_GAP threshold until there's
# enough data for the adaptive estimate to mean anything.
MIN_GAPS_FOR_ADAPTIVE_THRESHOLD = 3


def build_seats(candidates: list[CandidateSeat]) -> list[Seat]:
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda c: c[0].cy)
    ys = [c[0].cy for c in ordered]
    gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    if len(gaps) >= MIN_GAPS_FOR_ADAPTIVE_THRESHOLD:
        median_gap = sorted(gaps)[len(gaps) // 2]
        threshold = max(MIN_ROW_GAP, median_gap * ROW_GAP_FACTOR)
    else:
        threshold = MIN_ROW_GAP

    rows: list[list[CandidateSeat]] = [[ordered[0]]]
    for i in range(1, len(ordered)):
        if ys[i] - ys[i - 1] > threshold:
            rows.append([])
        rows[-1].append(ordered[i])

    seats: list[Seat] = []
    for row_index, row in enumerate(rows):
        row_sorted = sorted(row, key=lambda c: c[0].cx)
        label = _row_label(row_index)
        for col_index, (bbox, occupied, confidence) in enumerate(row_sorted):
            seats.append(
                Seat(
                    seat_id=f"{label}{col_index + 1}",
                    row_index=row_index,
                    col_index=col_index,
                    bbox=bbox,
                    occupied=occupied,
                    detection_confidence=confidence,
                )
            )
    return seats


def _row_label(index: int) -> str:
    """0 -> A, 1 -> B, ... 25 -> Z, 26 -> AA, matching spreadsheet-style labels."""
    index += 1
    letters = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
