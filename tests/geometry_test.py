#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose

# hwrt modules
import hwrt.geometry as geometry


# Tests
def object_creation_test():
    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(1, 1)
    geometry.LineSegment(p1, p2)
    geometry.BoundingBox(p1, p2)


def point_distance_test():
    a = geometry.Point(0, 0)
    b = geometry.Point(42, 0)
    nose.tools.assert_equal(a.dist_to(b), 42)
    nose.tools.assert_equal(b.dist_to(a), 42)


def line_segment_parallel_distance_test():
    """Test the distance of two parallel line segments."""
    # TODO: Other tests!
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    la = geometry.LineSegment(ap1, ap2)

    bp1 = geometry.Point(0, 1)
    bp2 = geometry.Point(1, 1)
    lb = geometry.LineSegment(bp1, bp2)

    nose.tools.assert_equal(la.dist_to(lb), 1)

    bp1 = geometry.Point(0, 2)
    bp2 = geometry.Point(1, 2)
    lb = geometry.LineSegment(bp1, bp2)

    nose.tools.assert_equal(la.dist_to(lb), 2)

    bp1 = geometry.Point(1, 2)
    bp2 = geometry.Point(2, 2)
    lb = geometry.LineSegment(bp1, bp2)

    nose.tools.assert_equal(la.dist_to(lb), 2)


def bounding_box_test():
    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(1, 1)
    bb = geometry.BoundingBox(p1, p2)
    nose.tools.assert_equal(bb.get_area(), 1)
    nose.tools.assert_equal(bb.get_width(), 1)
    nose.tools.assert_equal(bb.get_height(), 1)
    nose.tools.assert_equal(bb.get_largest_dimension(), 1)

    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(2, 2)
    bb = geometry.BoundingBox(p1, p2)
    nose.tools.assert_equal(bb.get_area(), 4)
    nose.tools.assert_equal(bb.get_width(), 2)
    nose.tools.assert_equal(bb.get_height(), 2)
    nose.tools.assert_equal(bb.get_largest_dimension(), 2)

    p1 = geometry.Point(0, 0)
    p2 = geometry.Point(3, 2)
    bb = geometry.BoundingBox(p1, p2)
    nose.tools.assert_equal(bb.get_area(), 6)
    nose.tools.assert_equal(bb.get_width(), 3)
    nose.tools.assert_equal(bb.get_height(), 2)
    nose.tools.assert_equal(bb.get_largest_dimension(), 3)


def bb_intersection_test():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(2, 2)
    bba = geometry.BoundingBox(ap1, ap2)

    # Test 1
    bp1 = geometry.Point(1, 1)
    bp2 = geometry.Point(2, 2)
    bbb = geometry.BoundingBox(bp1, bp2)
    nose.tools.assert_equal(geometry.do_bb_intersect(bba, bbb), True)

    # Test 2
    bp1 = geometry.Point(2, 2)
    bp2 = geometry.Point(3, 3)
    bbb = geometry.BoundingBox(bp1, bp2)
    nose.tools.assert_equal(geometry.do_bb_intersect(bba, bbb), True)

    # Test 3
    bp1 = geometry.Point(1, 1)
    bp2 = geometry.Point(3, 3)
    bbb = geometry.BoundingBox(bp1, bp2)
    nose.tools.assert_equal(geometry.do_bb_intersect(bba, bbb), True)

    # Test 3
    bp1 = geometry.Point(3, 3)
    bp2 = geometry.Point(4, 4)
    bbb = geometry.BoundingBox(bp1, bp2)
    nose.tools.assert_equal(geometry.do_bb_intersect(bba, bbb), False)


def segments_distance_test():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    la = geometry.LineSegment(ap1, ap2)

    # Test 1
    bp1 = geometry.Point(0, 1)
    bp2 = geometry.Point(1, 1)
    lb = geometry.LineSegment(bp1, bp2)
    nose.tools.assert_equal(geometry.segments_distance(la, lb), 1.0)

    # Test 2: Line segements cross
    bp1 = geometry.Point(0.5, 0.5)
    bp2 = geometry.Point(0.5, -0.5)
    lb = geometry.LineSegment(bp1, bp2)
    nose.tools.assert_equal(geometry.segments_distance(la, lb), 0)


def point_segment_distance_test():
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)

    # Test 1
    point = geometry.Point(0, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 0.0)

    # Test 2
    point = geometry.Point(0, 1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    # Test 3: Line segement is just a point
    line = geometry.LineSegment(ap1, ap1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    # Test 3: Line segement is a straight vertical line
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(1, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    point = geometry.Point(0, 2)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    point = geometry.Point(0, -1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap2 = geometry.Point(0, 0)
    ap1 = geometry.Point(0, 1)
    point = geometry.Point(0, -1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(0, -1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(0, 2)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(2, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(2, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-1, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 0)
    line = geometry.LineSegment(ap2, ap1)
    point = geometry.Point(-1, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 1.0)

    # Test 3: Line segement is a straight vertical line and point is on it
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(0, 0.1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 0)

    # Test 4: Vertical line tests
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(0.5, 0.5)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 0.5)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(0, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-0.5, 0.5)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line), 0.5)

    # Test 5: Other
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(1, 0)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line),
                            (2**0.5)/2.0)

    # Test 6: Continued line
    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(2, 2)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line),
                            2**0.5)

    ap1 = geometry.Point(0, 0)
    ap2 = geometry.Point(1, 1)
    line = geometry.LineSegment(ap1, ap2)
    point = geometry.Point(-1, -1)
    nose.tools.assert_equal(geometry.point_segment_distance(point, line),
                            2**0.5)


def segments_intersection_test():
    l1 = geometry.LineSegment(geometry.Point(0, 0), geometry.Point(2, 2))
    l2 = geometry.LineSegment(geometry.Point(1, 1), geometry.Point(3, 3))
    nose.tools.assert_equal(geometry.segments_intersect(l1, l2), True)

    l1 = geometry.LineSegment(geometry.Point(0, 0), geometry.Point(2, 2))
    l2 = geometry.LineSegment(geometry.Point(2.1, 2.1), geometry.Point(3, 3))
    nose.tools.assert_equal(geometry.segments_intersect(l1, l2), False)
