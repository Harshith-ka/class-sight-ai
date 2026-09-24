"""Turn raw detections into candidate seats with an occupied/empty call.

Every detected `chair` (COCO `chair`/`bench`, see detector.py) is a candidate
seat (spec section 17). Without a custom-trained occupied/empty classifier
(Phase 3), occupancy is inferred from whether a detected `person` overlaps or
sits centered on the chair.

Classroom desks frequently hide their own seating from a frontal/elevated
camera angle — the desk surface occludes the bench or chair tucked behind or
under it, so no amount of confidence tuning recovers a chair the detector
never had visual evidence for. As a fallback, any detected `desk` with no
chair/bench matched to it gets a seat inferred from the desk's own bounding
box (split into two side-by-side seats if the desk is wide enough to seat a
pair) — a lower-confidence proxy, not a real detection.
"""
from __future__ import annotations

from vision.models import BBox, Detection

OCCUPANCY_IOU_THRESHOLD = 0.08
OCCUPANCY_CENTER_MARGIN = 0.03

DESK_COVERAGE_IOU_THRESHOLD = 0.05
DESK_PAIR_ASPECT_RATIO = 2.2  # desk width > height * this -> inferred as a 2-seat bench
INFERRED_CONFIDENCE_FACTOR = 0.6  # desk-inferred seats are less certain than a real chair detection

CandidateSeat = tuple[BBox, bool, float]  # (seat_bbox, occupied, detection_confidence)


def detect_candidate_seats(detections: list[Detection]) -> list[CandidateSeat]:
    chairs = [d for d in detections if d.class_name == "chair"]
    desks = [d for d in detections if d.class_name == "desk"]
    persons = [d for d in detections if d.class_name == "person"]

    candidates: list[CandidateSeat] = []
    for chair in chairs:
        occupied = _is_occupied(chair.bbox, persons)
        candidates.append((chair.bbox, occupied, chair.confidence))

    chair_boxes = [c.bbox for c in chairs]
    for desk in desks:
        if any(desk.bbox.iou(box) > DESK_COVERAGE_IOU_THRESHOLD for box in chair_boxes):
            continue
        for seat_bbox in _infer_seats_from_desk(desk.bbox):
            occupied = _is_occupied(seat_bbox, persons)
            candidates.append((seat_bbox, occupied, desk.confidence * INFERRED_CONFIDENCE_FACTOR))

    return candidates


def _infer_seats_from_desk(desk_bbox: BBox) -> list[BBox]:
    if desk_bbox.height <= 0:
        return [desk_bbox]
    if desk_bbox.width > desk_bbox.height * DESK_PAIR_ASPECT_RATIO:
        mid = (desk_bbox.x1 + desk_bbox.x2) / 2
        return [
            BBox(desk_bbox.x1, desk_bbox.y1, mid, desk_bbox.y2),
            BBox(mid, desk_bbox.y1, desk_bbox.x2, desk_bbox.y2),
        ]
    return [desk_bbox]


def _is_occupied(seat_bbox: BBox, persons: list[Detection]) -> bool:
    expanded = seat_bbox.expanded(OCCUPANCY_CENTER_MARGIN, OCCUPANCY_CENTER_MARGIN)
    for person in persons:
        if seat_bbox.iou(person.bbox) > OCCUPANCY_IOU_THRESHOLD:
            return True
        if expanded.contains_point(person.bbox.cx, person.bbox.cy):
            return True
    return False
