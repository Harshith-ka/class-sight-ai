"""Per-seat geometry: distance, angle, occlusion, and position category
(spec sections 20-21).

The instructor's forward gaze direction can't be observed from a single
still image. By default it's approximated as pointing toward the
bottom-center of the frame (DEFAULT_FORWARD_TARGET) — a reasonable proxy for
"facing the class" in a typical front-of-room photo. If the user manually
marks the board position (spec section 29 "Adjust board position"), that
becomes the forward-direction reference instead — an instructor's gaze is
much better approximated as "toward the board" than "toward the bottom of
the frame," so this is a real accuracy improvement, not just a cosmetic
correction.
"""
from __future__ import annotations

from vision.geometry.vectors import angle_between_deg, vector
from vision.models import Detection, Instructor, Seat, euclidean
from vision.visibility.occlusion import compute_occlusion

DEFAULT_FORWARD_TARGET = (0.5, 1.0)


def compute_seat_geometry(
    seat: Seat,
    instructor: Instructor,
    all_detections: list[Detection],
    total_rows: int,
    seats_in_row: int,
    forward_target: tuple[float, float] = DEFAULT_FORWARD_TARGET,
) -> tuple[float, float, float, str]:
    seat_center = (seat.bbox.cx, seat.bbox.cy)

    raw_distance = euclidean(instructor.position, seat_center)

    forward_vec = vector(instructor.position, forward_target)
    to_seat_vec = vector(instructor.position, seat_center)
    raw_angle_deg = angle_between_deg(forward_vec, to_seat_vec)

    obstacles = [
        d.bbox
        for d in all_detections
        if d.class_name in ("person", "chair") and d.bbox is not seat.bbox
    ]
    occlusion = compute_occlusion(instructor.position, seat_center, obstacles)

    position_category = _position_category(seat, total_rows, seats_in_row)
    return raw_distance, raw_angle_deg, occlusion, position_category


def _position_category(seat: Seat, total_rows: int, seats_in_row: int) -> str:
    row_frac = seat.row_index / (total_rows - 1) if total_rows > 1 else 0.0
    col_frac = seat.col_index / (seats_in_row - 1) if seats_in_row > 1 else 0.5

    if row_frac < 0.34:
        depth = "front"
    elif row_frac > 0.66:
        depth = "rear"
    else:
        depth = "middle"

    if col_frac < 0.15 or col_frac > 0.85:
        side = "corner"
    elif col_frac < 0.34 or col_frac > 0.66:
        side = "side"
    else:
        side = "center"

    return f"{depth}-{side}"
