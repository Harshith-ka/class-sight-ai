from vision.models import BBox, Detection
from vision.seats.row_clustering import build_seats
from vision.seats.seat_detector import detect_candidate_seats


def _chair(x1, y1, x2, y2, conf=0.9):
    return Detection(class_name="chair", confidence=conf, bbox=BBox(x1, y1, x2, y2))


def _desk(x1, y1, x2, y2, conf=0.9):
    return Detection(class_name="desk", confidence=conf, bbox=BBox(x1, y1, x2, y2))


def _person(x1, y1, x2, y2, conf=0.9):
    return Detection(class_name="person", confidence=conf, bbox=BBox(x1, y1, x2, y2))


def test_occupied_when_person_overlaps_chair():
    chair = _chair(0.1, 0.1, 0.2, 0.3)
    person = _person(0.1, 0.05, 0.2, 0.25)
    candidates = detect_candidate_seats([chair, person])
    assert len(candidates) == 1
    assert candidates[0][1] is True


def test_empty_when_no_person_nearby():
    chair = _chair(0.1, 0.1, 0.2, 0.3)
    person = _person(0.7, 0.7, 0.8, 0.9)
    candidates = detect_candidate_seats([chair, person])
    assert candidates[0][1] is False


def test_row_clustering_two_rows():
    # Row 1 at y~0.2, row 2 at y~0.6, two chairs each.
    candidates = [
        (BBox(0.1, 0.15, 0.2, 0.25), False, 0.9),
        (BBox(0.3, 0.15, 0.4, 0.25), False, 0.9),
        (BBox(0.1, 0.55, 0.2, 0.65), False, 0.9),
        (BBox(0.3, 0.55, 0.4, 0.65), False, 0.9),
    ]
    seats = build_seats(candidates)
    rows = {s.row_index for s in seats}
    assert rows == {0, 1}
    assert len(seats) == 4


def test_row_clustering_seat_ids_ordered_left_to_right():
    candidates = [
        (BBox(0.3, 0.15, 0.4, 0.25), False, 0.9),
        (BBox(0.1, 0.15, 0.2, 0.25), False, 0.9),
    ]
    seats = build_seats(candidates)
    assert seats[0].seat_id == "A1"
    assert seats[0].bbox.x1 == 0.1
    assert seats[1].seat_id == "A2"
    assert seats[1].bbox.x1 == 0.3


def test_build_seats_empty_input():
    assert build_seats([]) == []


def test_row_clustering_two_far_apart_seats_split_into_two_rows():
    # Regression: with only one gap in the whole candidate set, an adaptive
    # median-based threshold is self-referential (gap > gap*1.6 is never
    # true), so two seats could never split into two rows no matter the
    # distance between them. See MIN_GAPS_FOR_ADAPTIVE_THRESHOLD.
    candidates = [
        (BBox(0.1, 0.1, 0.2, 0.2), False, 0.9),
        (BBox(0.3, 0.8, 0.4, 0.9), False, 0.9),
    ]
    seats = build_seats(candidates)
    rows = {s.row_index for s in seats}
    assert len(rows) == 2


def test_desk_with_no_chair_infers_one_seat():
    # Narrow desk (width < height * 2.2) -> a single inferred seat.
    desk = _desk(0.1, 0.1, 0.2, 0.3)
    candidates = detect_candidate_seats([desk])
    assert len(candidates) == 1
    assert candidates[0][2] < desk.confidence  # inferred confidence is discounted


def test_wide_desk_with_no_chair_infers_two_seats():
    # Wide desk (width > height * 2.2) -> split into two side-by-side seats.
    desk = _desk(0.1, 0.1, 0.6, 0.2)
    candidates = detect_candidate_seats([desk])
    assert len(candidates) == 2
    left, right = sorted(candidates, key=lambda c: c[0].x1)
    assert left[0].x2 == right[0].x1  # seats split the desk with no gap or overlap


def test_desk_already_covered_by_chair_is_not_inferred():
    chair = _chair(0.12, 0.12, 0.18, 0.28)
    desk = _desk(0.1, 0.1, 0.2, 0.3)
    candidates = detect_candidate_seats([chair, desk])
    assert len(candidates) == 1  # only the real chair, no duplicate inferred seat


def test_desk_seat_occupancy_uses_person_overlap():
    desk = _desk(0.1, 0.1, 0.2, 0.3)
    person = _person(0.1, 0.1, 0.2, 0.3)
    candidates = detect_candidate_seats([desk, person])
    assert candidates[0][1] is True
