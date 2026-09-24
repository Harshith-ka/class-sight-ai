"""Export a corrected analysis as a YOLO-format training sample.

Phase 1 has no custom-trained model — see AGENTS roadmap Phase 3. Training
one requires a labeled dataset, and we don't have one yet. But every manual
correction a user makes in the app (add/delete seat, move instructor) is
already a human-verified ground-truth label. This module turns the *current*
state of a session — after any corrections — into one YOLO training sample:
the original image plus a label file with one box per seat (class 0) and,
if present, the instructor (class 1).

This is an explicit, user-triggered action (the "Export Training Data"
button), not automatic background collection — matching the spec's privacy
principle (section 47) of not using uploaded images for training without
explicit permission. Nothing is exported unless the user asks for it.
"""
from __future__ import annotations

from pathlib import Path

import cv2

from app.services.session_store import AnalysisSession
from vision.models import BBox

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAINING_DATA_DIR = PROJECT_ROOT / "ml" / "training_data"
IMAGES_DIR = TRAINING_DATA_DIR / "images"
LABELS_DIR = TRAINING_DATA_DIR / "labels"

SEAT_CLASS_ID = 0
INSTRUCTOR_CLASS_ID = 1
CLASS_NAMES = ["seat", "instructor"]

# Synthetic box for a manually-placed instructor with no detected bbox:
# feet at `position`, extending upward — a rough standing-person proportion,
# not a real measurement.
SYNTHETIC_INSTRUCTOR_HALF_WIDTH = 0.05
SYNTHETIC_INSTRUCTOR_HEIGHT = 0.3


def export_training_sample(session: AnalysisSession) -> dict:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)

    image_path = IMAGES_DIR / f"{session.analysis_id}.jpg"
    label_path = LABELS_DIR / f"{session.analysis_id}.txt"

    if not cv2.imwrite(str(image_path), session.image_bgr):
        raise RuntimeError("Failed to write training image")

    lines = [_yolo_line(SEAT_CLASS_ID, seat.bbox) for seat in session.outcome.seats]

    instructor = session.outcome.instructor
    instructor_included = instructor is not None
    if instructor is not None:
        bbox = instructor.bbox or _synthesize_instructor_bbox(instructor.position)
        lines.append(_yolo_line(INSTRUCTOR_CLASS_ID, bbox))

    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    _ensure_dataset_yaml()

    return {
        "image_path": str(image_path),
        "label_path": str(label_path),
        "seat_count": len(session.outcome.seats),
        "instructor_included": instructor_included,
    }


def _yolo_line(class_id: int, bbox: BBox) -> str:
    return f"{class_id} {bbox.cx:.6f} {bbox.cy:.6f} {bbox.width:.6f} {bbox.height:.6f}"


def _synthesize_instructor_bbox(position: tuple[float, float]) -> BBox:
    x, y = position
    return BBox(
        max(0.0, x - SYNTHETIC_INSTRUCTOR_HALF_WIDTH),
        max(0.0, y - SYNTHETIC_INSTRUCTOR_HEIGHT),
        min(1.0, x + SYNTHETIC_INSTRUCTOR_HALF_WIDTH),
        min(1.0, y),
    )


def _ensure_dataset_yaml() -> None:
    yaml_path = TRAINING_DATA_DIR / "data.yaml"
    if yaml_path.exists():
        return
    names_block = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASS_NAMES))
    yaml_path.write_text(
        "# Auto-generated. Fed by the app's 'Export Training Data' action (Phase 1 -> Phase 3 bridge).\n"
        "path: .\n"
        "train: images\n"
        "val: images\n"
        f"names:\n{names_block}\n",
        encoding="utf-8",
    )
