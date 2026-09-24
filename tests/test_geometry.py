import math

from vision.geometry.vectors import angle_between_deg, clamp, magnitude, vector
from vision.models import BBox


def test_bbox_iou_no_overlap():
    a = BBox(0, 0, 0.1, 0.1)
    b = BBox(0.5, 0.5, 0.6, 0.6)
    assert a.iou(b) == 0.0


def test_bbox_iou_full_overlap():
    a = BBox(0.1, 0.1, 0.4, 0.4)
    assert a.iou(a) == 1.0


def test_bbox_iou_partial_overlap():
    a = BBox(0.0, 0.0, 0.2, 0.2)
    b = BBox(0.1, 0.1, 0.3, 0.3)
    iou = a.iou(b)
    assert 0.0 < iou < 1.0


def test_bbox_contains_point():
    box = BBox(0.2, 0.2, 0.4, 0.4)
    assert box.contains_point(0.3, 0.3)
    assert not box.contains_point(0.5, 0.5)


def test_bbox_intersects_segment_true():
    box = BBox(0.4, 0.4, 0.6, 0.6)
    assert box.intersects_segment((0.0, 0.5), (1.0, 0.5))


def test_bbox_intersects_segment_false():
    box = BBox(0.4, 0.4, 0.6, 0.6)
    assert not box.intersects_segment((0.0, 0.0), (0.1, 0.1))


def test_vector_and_magnitude():
    v = vector((0.0, 0.0), (3.0, 4.0))
    assert v == (3.0, 4.0)
    assert magnitude(v) == 5.0


def test_angle_between_deg_parallel():
    assert angle_between_deg((1, 0), (2, 0)) == 0.0


def test_angle_between_deg_perpendicular():
    assert math.isclose(angle_between_deg((1, 0), (0, 1)), 90.0)


def test_angle_between_deg_opposite():
    assert math.isclose(angle_between_deg((1, 0), (-1, 0)), 180.0)


def test_clamp_bounds():
    assert clamp(150) == 100
    assert clamp(-10) == 0
    assert clamp(50) == 50
