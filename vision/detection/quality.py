"""Pre-inference image quality checks (spec section 6).

Cheap, deterministic, OpenCV-only checks that run before the detector so a
low-quality upload gets a clear rejection message instead of a garbage
analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

MIN_WIDTH = 1280
MIN_HEIGHT = 720
BLUR_THRESHOLD = 80.0  # Laplacian variance below this = too blurry
DARK_MEAN_THRESHOLD = 40.0
BRIGHT_MEAN_THRESHOLD = 235.0
LOW_CONTRAST_STD_THRESHOLD = 15.0
QUALITY_PASS_THRESHOLD = 45


@dataclass
class QualityReport:
    resolution_score: int
    brightness_score: int
    sharpness_score: int
    contrast_score: int
    overall: int
    width: int
    height: int
    passed: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "resolution": _label(self.resolution_score),
            "brightness": _label(self.brightness_score),
            "sharpness": _label(self.sharpness_score),
            "contrast": _label(self.contrast_score),
            "overall": self.overall,
            "width": self.width,
            "height": self.height,
            "passed": self.passed,
            "reasons": self.reasons,
        }


def _label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Moderate"
    return "Poor"


def assess_quality(image_bgr: np.ndarray) -> QualityReport:
    height, width = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    reasons: list[str] = []

    # Resolution
    res_ratio = min(width / MIN_WIDTH, height / MIN_HEIGHT)
    resolution_score = int(np.clip(res_ratio * 80, 0, 100))
    if res_ratio < 1.0:
        reasons.append("Resolution is below the recommended 720p minimum.")

    # Brightness (mean luma)
    mean_brightness = float(gray.mean())
    if mean_brightness < DARK_MEAN_THRESHOLD:
        brightness_score = int(np.clip(mean_brightness / DARK_MEAN_THRESHOLD * 60, 0, 60))
        reasons.append("Image is quite dark; detection accuracy may drop.")
    elif mean_brightness > BRIGHT_MEAN_THRESHOLD:
        brightness_score = int(np.clip((255 - mean_brightness) / (255 - BRIGHT_MEAN_THRESHOLD) * 60, 0, 60))
        reasons.append("Image is overexposed; detection accuracy may drop.")
    else:
        brightness_score = 100

    # Sharpness (variance of Laplacian)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness_score = int(np.clip(laplacian_var / BLUR_THRESHOLD * 70, 0, 100))
    if laplacian_var < BLUR_THRESHOLD:
        reasons.append("Image appears blurry.")

    # Contrast (std dev of luma)
    contrast_std = float(gray.std())
    contrast_score = int(np.clip(contrast_std / LOW_CONTRAST_STD_THRESHOLD * 70, 0, 100))
    if contrast_std < LOW_CONTRAST_STD_THRESHOLD:
        reasons.append("Image has low contrast.")

    overall = int(
        0.30 * resolution_score
        + 0.25 * sharpness_score
        + 0.25 * brightness_score
        + 0.20 * contrast_score
    )

    passed = overall >= QUALITY_PASS_THRESHOLD and width > 0 and height > 0
    if not passed and not reasons:
        reasons.append("Overall image quality is too low for reliable detection.")

    return QualityReport(
        resolution_score=resolution_score,
        brightness_score=brightness_score,
        sharpness_score=sharpness_score,
        contrast_score=contrast_score,
        overall=overall,
        width=width,
        height=height,
        passed=passed,
        reasons=reasons,
    )
