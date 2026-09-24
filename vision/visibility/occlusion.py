"""Line-of-sight occlusion estimate (spec section 21).

Draws the instructor -> seat segment and checks whether other detected
people/furniture bounding boxes cross it. This is a 2D geometric proxy for
occlusion, not a true 3D line-of-sight simulation — a single photo can't
tell us head height or torso pose, so this is documented as an estimate
throughout the UI (spec section 68).
"""
from __future__ import annotations

from vision.models import BBox

OCCLUSION_PER_HIT = 0.35
MAX_OCCLUSION = 1.0


def compute_occlusion(
    instructor_pos: tuple[float, float],
    seat_center: tuple[float, float],
    obstacles: list[BBox],
) -> float:
    hits = 0
    for bbox in obstacles:
        if bbox.contains_point(*seat_center):
            continue  # the seat's own occupant isn't an obstruction to themselves
        if bbox.intersects_segment(instructor_pos, seat_center):
            hits += 1
    return min(MAX_OCCLUSION, hits * OCCLUSION_PER_HIT)
