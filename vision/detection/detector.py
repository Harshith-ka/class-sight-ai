"""Pretrained YOLO object detector wrapper.

Phase 1 uses stock COCO weights (no custom classroom classes yet — see
AGENTS roadmap Phase 3 for fine-tuning). Detections are filtered to the
classes relevant to classroom analysis and normalized to [0, 1] coordinates.

Tuning choices found by inspecting raw detections on real classroom photos:

- `yolov8n` (nano) is too weak for furniture at typical classroom camera
  distance — real chairs scored ~0.45 confidence at best. `yolov8s` at a
  higher inference resolution (imgsz=1280 vs the 640 default) roughly
  doubles confidence on the same chairs and surfaces far more of them.
- COCO classifies classroom benches/desks as `bench`, not `chair` or
  `dining table` — without including it, whole rows of bench seating are
  silently dropped.
- Even at imgsz=1280, a chair far from the camera in a wide classroom shot
  can still be only a few dozen pixels tall — below what a single full-image
  pass reliably resolves. Sliced/tiled inference (vision/detection/tiling.py)
  runs the same model again on overlapping crops of the image at their own
  resolution, recovering detail a single downscaled pass loses, at the cost
  of extra forward passes.

Isolated behind ObjectDetector so Phase 3 can swap in a fine-tuned
classroom-specific model without touching any downstream code
(spec section 54 module separation).
"""
from __future__ import annotations

import numpy as np

from vision.detection.tiling import make_tiles
from vision.models import BBox, Detection

# COCO class names we care about for classroom analysis.
RELEVANT_CLASSES = {"person", "chair", "bench", "dining table", "laptop", "backpack", "tv"}

# Map COCO's generic names onto the vocabulary the rest of the pipeline uses.
# `bench` is treated as a seat candidate alongside `chair` — classroom desks
# with attached bench seating are common and otherwise invisible to the
# seat detector.
CLASS_ALIASES = {
    "dining table": "desk",
    "tv": "screen",
    "bench": "chair",
}

# Classes prone to duplicate/overlapping detections: `chair` because
# bench->chair aliasing means the same physical object can surface under two
# original COCO classes, `desk` because large table surfaces often get boxed
# more than once at different scales, and `person` because tiled inference
# means the same person can be picked up by the full-image pass and by one
# or more overlapping tiles.
DEDUPLICATE_CLASSES = {"chair", "desk", "person"}
DEDUPLICATE_IOU_THRESHOLD = 0.5


class ObjectDetector:
    """Thin wrapper around an Ultralytics YOLO model with optional tiled inference."""

    def __init__(
        self,
        weights: str = "yolov8s.pt",
        confidence_threshold: float = 0.2,
        imgsz: int = 1280,
        tile_imgsz: int = 960,
        use_tiling: bool = True,
    ):
        from ultralytics import YOLO  # imported lazily: heavy dependency

        self.model = YOLO(weights)
        self.confidence_threshold = confidence_threshold
        self.imgsz = imgsz
        self.tile_imgsz = tile_imgsz
        self.use_tiling = use_tiling

    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        height, width = image_bgr.shape[:2]

        detections = self._predict_region(image_bgr, offset=(0, 0), full_size=(width, height), imgsz=self.imgsz)

        if self.use_tiling:
            for x1, y1, x2, y2 in make_tiles(width, height):
                tile = image_bgr[y1:y2, x1:x2]
                if tile.size == 0:
                    continue
                detections.extend(
                    self._predict_region(tile, offset=(x1, y1), full_size=(width, height), imgsz=self.tile_imgsz)
                )

        return _deduplicate(detections)

    def _predict_region(
        self,
        region: np.ndarray,
        offset: tuple[int, int],
        full_size: tuple[int, int],
        imgsz: int,
    ) -> list[Detection]:
        offset_x, offset_y = offset
        full_width, full_height = full_size
        results = self.model.predict(region, conf=self.confidence_threshold, imgsz=imgsz, verbose=False)

        detections: list[Detection] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_name = names[int(box.cls[0])]
                if class_name not in RELEVANT_CLASSES:
                    continue
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
                confidence = float(box.conf[0])
                detections.append(
                    Detection(
                        class_name=CLASS_ALIASES.get(class_name, class_name),
                        confidence=confidence,
                        bbox=BBox(
                            (x1 + offset_x) / full_width,
                            (y1 + offset_y) / full_height,
                            (x2 + offset_x) / full_width,
                            (y2 + offset_y) / full_height,
                        ),
                    )
                )
        return detections


def _deduplicate(detections: list[Detection]) -> list[Detection]:
    """Cross-source NMS for classes where tiling/aliasing can produce
    duplicates (e.g. the same chair detected as both `chair` and `bench`, or
    the same person picked up by the full pass and an overlapping tile)."""
    kept: list[Detection] = []
    for class_name in {d.class_name for d in detections}:
        group = sorted(
            (d for d in detections if d.class_name == class_name),
            key=lambda d: -d.confidence,
        )
        if class_name not in DEDUPLICATE_CLASSES:
            kept.extend(group)
            continue
        survivors: list[Detection] = []
        for det in group:
            if all(det.bbox.iou(s.bbox) < DEDUPLICATE_IOU_THRESHOLD for s in survivors):
                survivors.append(det)
        kept.extend(survivors)
    return kept
