"""Small 2D vector/geometry helpers shared across the visibility engine."""
from __future__ import annotations

import math

Point = tuple[float, float]


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def vector(p_from: Point, p_to: Point) -> Point:
    return (p_to[0] - p_from[0], p_to[1] - p_from[1])


def magnitude(v: Point) -> float:
    return math.hypot(v[0], v[1])


def angle_between_deg(v1: Point, v2: Point) -> float:
    """Unsigned angle in degrees between two 2D vectors, 0-180."""
    m1, m2 = magnitude(v1), magnitude(v2)
    if m1 == 0 or m2 == 0:
        return 0.0
    cos_theta = (v1[0] * v2[0] + v1[1] * v2[1]) / (m1 * m2)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))
