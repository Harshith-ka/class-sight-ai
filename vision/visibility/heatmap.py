"""Overlay a seat-score heatmap on the original classroom image (spec section 23)."""
from __future__ import annotations

import base64

import cv2
import numpy as np

from vision.models import Instructor, Seat

GREEN = (76, 175, 80)
YELLOW = (255, 193, 7)
ORANGE = (255, 152, 0)
RED = (244, 67, 54)


def _color_for_score(score: float) -> tuple[int, int, int]:
    if score >= 75:
        rgb = GREEN
    elif score >= 55:
        rgb = YELLOW
    elif score >= 35:
        rgb = ORANGE
    else:
        rgb = RED
    return rgb[::-1]  # cv2 expects BGR


def generate_heatmap(image_bgr: np.ndarray, seats: list[Seat], instructor: Instructor | None) -> str:
    height, width = image_bgr.shape[:2]
    overlay = image_bgr.copy()

    for seat in seats:
        color = _color_for_score(seat.scores.final)
        x1, y1 = int(seat.bbox.x1 * width), int(seat.bbox.y1 * height)
        x2, y2 = int(seat.bbox.x2 * width), int(seat.bbox.y2 * height)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness=-1)

    blended = cv2.addWeighted(overlay, 0.35, image_bgr, 0.65, 0)

    for seat in seats:
        color = _color_for_score(seat.scores.final)
        x1, y1 = int(seat.bbox.x1 * width), int(seat.bbox.y1 * height)
        x2, y2 = int(seat.bbox.x2 * width), int(seat.bbox.y2 * height)
        cv2.rectangle(blended, (x1, y1), (x2, y2), color, thickness=2)
        label = f"{seat.seat_id} {int(seat.scores.final)}"
        cv2.putText(
            blended, label, (x1 + 2, max(12, y1 + 14)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA,
        )

    if instructor is not None:
        ix, iy = int(instructor.position[0] * width), int(instructor.position[1] * height)
        cv2.drawMarker(blended, (ix, iy), (255, 255, 255), markerType=cv2.MARKER_STAR, markerSize=20, thickness=2)

    success, buffer = cv2.imencode(".png", blended)
    if not success:
        raise RuntimeError("Failed to encode heatmap image")
    return base64.b64encode(buffer).decode("ascii")
