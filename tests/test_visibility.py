from vision.models import BBox, Detection, Instructor, Seat
from vision.visibility.instructor import detect_instructor
from vision.visibility.occlusion import compute_occlusion
from vision.visibility.scorer import score_seats
from vision.visibility.visibility_engine import compute_seat_geometry


def _seat(seat_id, x1, y1, x2, y2, row=0, col=0, conf=0.9):
    return Seat(
        seat_id=seat_id, row_index=row, col_index=col,
        bbox=BBox(x1, y1, x2, y2), occupied=False, detection_confidence=conf,
    )


def test_detect_instructor_prefers_top_centered_person():
    top_centered = Detection("person", 0.9, BBox(0.45, 0.05, 0.55, 0.3))
    bottom_side = Detection("person", 0.9, BBox(0.8, 0.7, 0.9, 0.95))
    instructor = detect_instructor([top_centered, bottom_side])
    assert instructor is not None
    assert instructor.bbox == top_centered.bbox


def test_detect_instructor_no_persons_returns_none():
    assert detect_instructor([]) is None


def test_compute_occlusion_no_obstacles():
    assert compute_occlusion((0.5, 0.0), (0.5, 1.0), []) == 0.0


def test_compute_occlusion_blocking_object_increases_score():
    blocker = BBox(0.4, 0.4, 0.6, 0.6)
    occlusion = compute_occlusion((0.5, 0.0), (0.5, 1.0), [blocker])
    assert occlusion > 0.0


def test_compute_occlusion_ignores_box_containing_seat_itself():
    seat_box = BBox(0.45, 0.9, 0.55, 1.0)
    occlusion = compute_occlusion((0.5, 0.0), (0.5, 0.95), [seat_box])
    assert occlusion == 0.0


def test_score_seats_front_seat_scores_lower_than_rear_seat():
    instructor = Instructor(position=(0.5, 0.05), confidence=0.9)
    front = _seat("A1", 0.45, 0.15, 0.55, 0.25, row=0, col=0)
    rear = _seat("C1", 0.45, 0.75, 0.55, 0.85, row=2, col=0)
    seats = [front, rear]
    detections = [
        Detection("chair", 0.9, front.bbox),
        Detection("chair", 0.9, rear.bbox),
    ]
    score_seats(seats, instructor, detections)
    assert front.scores.final < rear.scores.final
    assert front.explanation and rear.explanation


def test_score_seats_occluded_seat_scores_higher_than_clear_seat():
    instructor = Instructor(position=(0.5, 0.0), confidence=0.9)
    clear = _seat("A1", 0.05, 0.45, 0.15, 0.55, row=0, col=0)
    occluded = _seat("A2", 0.45, 0.85, 0.55, 0.95, row=0, col=1)
    blocker = Detection("person", 0.9, BBox(0.4, 0.4, 0.6, 0.6))
    seats = [clear, occluded]
    detections = [
        Detection("chair", 0.9, clear.bbox),
        Detection("chair", 0.9, occluded.bbox),
        blocker,
    ]
    score_seats(seats, instructor, detections)
    assert occluded.scores.occlusion > clear.scores.occlusion


def test_compute_seat_geometry_position_category_front_center():
    instructor = Instructor(position=(0.5, 0.0), confidence=0.9)
    seat = _seat("A2", 0.45, 0.05, 0.55, 0.15, row=0, col=1)
    _, _, _, category = compute_seat_geometry(seat, instructor, [], total_rows=3, seats_in_row=3)
    assert category == "front-center"


def test_compute_seat_geometry_custom_forward_target_changes_angle():
    instructor = Instructor(position=(0.5, 0.0), confidence=0.9)
    seat = _seat("A1", 0.85, 0.05, 0.95, 0.15, row=0, col=0)  # off to the side, same row as instructor

    _, angle_default, _, _ = compute_seat_geometry(seat, instructor, [], total_rows=1, seats_in_row=1)
    _, angle_toward_seat, _, _ = compute_seat_geometry(
        seat, instructor, [], total_rows=1, seats_in_row=1, forward_target=(0.9, 0.1)
    )
    assert angle_toward_seat < angle_default


def test_score_seats_respects_custom_forward_target():
    instructor = Instructor(position=(0.5, 0.0), confidence=0.9)

    default_seat = _seat("A1", 0.85, 0.05, 0.95, 0.15, row=0, col=0)
    score_seats([default_seat], instructor, [Detection("chair", 0.9, default_seat.bbox)])

    board_facing_seat = _seat("A1", 0.85, 0.05, 0.95, 0.15, row=0, col=0)
    score_seats(
        [board_facing_seat], instructor, [Detection("chair", 0.9, board_facing_seat.bbox)],
        forward_target=(0.9, 0.1),
    )

    assert board_facing_seat.scores.angle < default_seat.scores.angle
