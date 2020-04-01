#!/usr/bin/env python

# First party modules
import hwrt.geometry as geometry


def test_object_creation():
    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(1, 1)
    assert str(p1) == "p(0.00, 0.00)"
    geometry.LineSegment(p1, p2)
    geometry.BoundingBox(p1, p2)
    geometry.PolygonalChain([{"x": 0, "y": 0}, {"x": 10, "y": 5}, {"x": 2, "y": 3}])


def test_point_distance():
    a = geometry.Point(0, 0)
    b = geometry.Point(42, 0)
    assert a.dist_to(b) == 42
    assert b.dist_to(a) == 42


def test_line_segment_parallel_distance():
    """Test the distance of two parallel line segments."""
    # TODO: Other tests!
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    la = geometry.LineSegment(ap1, ap2)

    bp1 = geometry.Point(0, 1)
    bp2 = geometry.Point(1, 1)
    lb = geometry.LineSegment(bp1, bp2)

    assert la.dist_to(lb) == 1

    bp1 = geometry.Point(0, 2)
    bp2 = geometry.Point(1, 2)
    lb = geometry.LineSegment(bp1, bp2)

    assert la.dist_to(lb) == 2

    bp1 = geometry.Point(1, 2)
    bp2 = geometry.Point(2, 2)
    lb = geometry.LineSegment(bp1, bp2)

    assert la.dist_to(lb) == 2


def test_bounding_box():
    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(1, 1)
    bb = geometry.BoundingBox(p1, p2)
    assert bb.get_area() == 1
    assert bb.get_width() == 1
    assert bb.get_height() == 1
    assert bb.get_largest_dimension() == 1

    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(2, 2)
    bb = geometry.BoundingBox(p1, p2)
    assert bb.get_area() == 4
    assert bb.get_width() == 2
    assert bb.get_height() == 2
    assert bb.get_largest_dimension() == 2

    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(3, 2)
    bb = geometry.BoundingBox(p1, p2)
    assert bb.get_area() == 6
    assert bb.get_width() == 3
    assert bb.get_height() == 2
    assert bb.get_largest_dimension() == 3


def test_bb_intersection():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(2, 2)
    bba = geometry.BoundingBox(ap1, ap2)

    # Test 1
    bp1 = geometry.Point(1, 1)
    bp2 = geometry.Point(2, 2)
    bbb = geometry.BoundingBox(bp1, bp2)
    assert geometry.do_bb_intersect(bba, bbb)

    # Test 2
    bp1 = geometry.Point(2, 2)
    bp2 = geometry.Point(3, 3)
    bbb = geometry.BoundingBox(bp1, bp2)
    assert geometry.do_bb_intersect(bba, bbb)

    # Test 3
    bp1 = geometry.Point(1, 1)
    bp2 = geometry.Point(3, 3)
    bbb = geometry.BoundingBox(bp1, bp2)
    assert geometry.do_bb_intersect(bba, bbb)

    # Test 3
    bp1 = geometry.Point(3, 3)
    bp2 = geometry.Point(4, 4)
    bbb = geometry.BoundingBox(bp1, bp2)
    assert not geometry.do_bb_intersect(bba, bbb)


def test_segments_distance():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    la = geometry.LineSegment(ap1, ap2)

    # Test 1
    bp1 = geometry.Point(0, 1)
    bp2 = geometry.Point(1, 1)
    lb = geometry.LineSegment(bp1, bp2)
    assert geometry.segments_distance(la, lb) == 1.0

    # Test 2: Line segements cross
    bp1 = geometry.Point(0.5, 0.5)
    bp2 = geometry.Point(0.5, -0.5)
    lb = geometry.LineSegment(bp1, bp2)
    assert geometry.segments_distance(la, lb) == 0


def test_point_segment_distance():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)

    # Test 1
    point = geometry.Point(0, 0)
    assert geometry.point_segment_distance(point, line) == 0.0

    # Test 2
    point = geometry.Point(0, 1)
    assert geometry.point_segment_distance(point, line) == 1.0

    # Test 3: Line segement is just a point
    line = geometry.LineSegment(ap1, ap1)
    assert geometry.point_segment_distance(point, line) == 1.0

    # Test 3: Line segement is a straight vertical line
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(1, 0)
    assert geometry.point_segment_distance(point, line) == 1.0

    point = geometry.Point(0, 2)
    assert geometry.point_segment_distance(point, line) == 1.0

    point = geometry.Point(0, -1)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap2 = geometry.Point(0, 0)
    ap1 = geometry.Point(0, 1)
    point = geometry.Point(0, -1)
    assert geometry.point_segment_distance(point, line), 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(0, -1)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(0, 2)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(2, 0)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(2, 0)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-1, 0)
    assert geometry.point_segment_distance(point, line) == 1.0

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(-1, 0)
    assert geometry.point_segment_distance(point, line) == 1.0

    # Test 3: Line segement is a straight vertical line and point is on it
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(0, 0.1)
    assert geometry.point_segment_distance(point, line) == 0

    # Test 4: Vertical line tests
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(0.5, 0.5)
    assert geometry.point_segment_distance(point, line) == 0.5

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-0.5, 0.5)
    assert geometry.point_segment_distance(point, line) == 0.5

    # Test 5: Other
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(1, 0)
    assert geometry.point_segment_distance(point, line) == (2 ** 0.5) / 2.0

    # Test 6: Continued line
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(2, 2)
    assert geometry.point_segment_distance(point, line) == 2 ** 0.5

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-1, -1)
    assert geometry.point_segment_distance(point, line) == 2 ** 0.5


def test_segments_intersection():
    l1 = geometry.LineSegment(geometry.Point(0, 0), geometry.Point(2, 2))
    l2 = geometry.LineSegment(geometry.Point(1, 1), geometry.Point(3, 3))
    assert geometry.get_segments_intersections(l1, l2) == [geometry.Point(1, 1)]

    l1 = geometry.LineSegment(geometry.Point(0, 0), geometry.Point(2, 2))
    l2 = geometry.LineSegment(geometry.Point(2.1, 2.1), geometry.Point(3, 3))
    assert geometry.get_segments_intersections(l1, l2) == []

    # 2 vertical line segments
    l1 = geometry.LineSegment(geometry.Point(42, 2), geometry.Point(42, 0))
    l2 = geometry.LineSegment(geometry.Point(42, 1), geometry.Point(42, -1))
    assert geometry.get_segments_intersections(l1, l2) == [geometry.Point(42, 0)]

    l1 = geometry.LineSegment(geometry.Point(-1, 0), geometry.Point(1, 0))
    l2 = geometry.LineSegment(geometry.Point(0, -1), geometry.Point(0, 1))
    assert geometry.get_segments_intersections(l1, l2) == [geometry.Point(0, 0)]


def test_segment_intersection():
    l1 = geometry.LineSegment(geometry.Point(289, 69), geometry.Point(290, 69))
    l2 = geometry.LineSegment(geometry.Point(291, 69), geometry.Point(292, 69))
    assert geometry.get_segments_intersections(l1, l2) == []

    l1 = geometry.LineSegment(geometry.Point(0, 0), geometry.Point(0, 10))
    l2 = geometry.LineSegment(geometry.Point(5, 5), geometry.Point(2, 0))
    assert geometry.get_segments_intersections(l1, l2) == []


def test_stroke_selfintersection():
    a = [
        {"y": 69, "x": 289},
        {"y": 69, "x": 290},
        {"y": 69, "x": 291},
        {"y": 69, "x": 292},
        {"y": 69, "x": 293},
        {"y": 69, "x": 295},
        {"y": 70, "x": 297},
        {"y": 70, "x": 299},
        {"y": 71, "x": 302},
        {"y": 72, "x": 303},
    ]
    a = geometry.PolygonalChain(a)
    assert a.count_selfintersections() == 0
