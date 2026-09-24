"""Shared data structures for the CV/geometry pipeline.

All coordinates are normalized to [0, 1] relative to image width/height so the
pipeline is resolution-independent (spec section 18).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    def iou(self, other: "BBox") -> float:
        ix1, iy1 = max(self.x1, other.x1), max(self.y1, other.y1)
        ix2, iy2 = min(self.x2, other.x2), min(self.y2, other.y2)
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        inter = (ix2 - ix1) * (iy2 - iy1)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def expanded(self, margin_x: float, margin_y: float) -> "BBox":
        return BBox(
            self.x1 - margin_x, self.y1 - margin_y,
            self.x2 + margin_x, self.y2 + margin_y,
        )

    def contains_point(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def intersects_segment(self, p1: tuple[float, float], p2: tuple[float, float]) -> bool:
        """Liang-Barsky segment/box intersection test."""
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        t0, t1 = 0.0, 1.0
        for p, q in (
            (-dx, x1 - self.x1), (dx, self.x2 - x1),
            (-dy, y1 - self.y1), (dy, self.y2 - y1),
        ):
            if p == 0:
                if q < 0:
                    return False
                continue
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                if r < t1:
                    t1 = r
        return True


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: BBox


@dataclass
class Instructor:
    position: tuple[float, float]  # (x, y) normalized point used as origin for geometry
    confidence: float
    bbox: BBox | None = None
    source: str = "heuristic"  # "heuristic" | "manual"


@dataclass
class SeatScores:
    distance: float = 0.0
    occlusion: float = 0.0
    angle: float = 0.0
    position: float = 0.0
    confidence: float = 0.0
    final: float = 0.0
    raw_distance: float = 0.0
    raw_visibility: float = 0.0
    raw_angle_deg: float = 0.0


@dataclass
class Seat:
    seat_id: str
    row_index: int
    col_index: int
    bbox: BBox
    occupied: bool
    detection_confidence: float
    position_category: str = "center"
    scores: SeatScores = field(default_factory=SeatScores)
    explanation: list[str] = field(default_factory=list)
    manual: bool = False


def euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
