from app.services import corrections
from vision.models import BBox, Seat
from vision.pipeline import AnalysisOutcome


def _seat(seat_id, x1, y1, x2, y2, row=0, col=0, manual=False):
    return Seat(
        seat_id=seat_id, row_index=row, col_index=col,
        bbox=BBox(x1, y1, x2, y2), occupied=False, detection_confidence=0.8, manual=manual,
    )


def _outcome(seats: list[Seat]) -> AnalysisOutcome:
    return AnalysisOutcome(quality_dict={"overall": 80}, detections=[], seats=seats, instructor=None)


def test_move_board_sets_position():
    outcome = _outcome([])
    corrections.move_board(outcome, 0.4, 0.1)
    assert outcome.board_position == (0.4, 0.1)


def test_move_seat_updates_center_and_preserves_size():
    seat = _seat("A1", 0.1, 0.1, 0.2, 0.2)
    outcome = _outcome([seat])

    assert corrections.move_seat(outcome, "A1", 0.8, 0.8) is True

    moved = outcome.seats[0]
    assert abs(moved.bbox.cx - 0.8) < 1e-6
    assert abs(moved.bbox.cy - 0.8) < 1e-6
    assert abs(moved.bbox.width - seat.bbox.width) < 1e-6
    assert abs(moved.bbox.height - seat.bbox.height) < 1e-6
    assert moved.manual is True


def test_move_seat_clamps_within_frame_bounds():
    seat = _seat("A1", 0.0, 0.0, 0.2, 0.2)
    outcome = _outcome([seat])

    corrections.move_seat(outcome, "A1", -0.5, -0.5)

    moved = outcome.seats[0]
    assert moved.bbox.x1 >= 0.0
    assert moved.bbox.y1 >= 0.0


def test_move_seat_can_change_row_via_reclustering():
    # Move a seat far enough down that it should end up in its own new row.
    seat_a = _seat("A1", 0.1, 0.1, 0.2, 0.2)
    seat_b = _seat("A2", 0.3, 0.1, 0.4, 0.2)
    outcome = _outcome([seat_a, seat_b])

    corrections.move_seat(outcome, "A1", 0.15, 0.9)

    rows = {s.row_index for s in outcome.seats}
    assert len(rows) == 2  # the moved seat is now in a different row than A2


def test_move_seat_unknown_id_returns_false():
    outcome = _outcome([_seat("A1", 0.1, 0.1, 0.2, 0.2)])
    assert corrections.move_seat(outcome, "Z9", 0.5, 0.5) is False
