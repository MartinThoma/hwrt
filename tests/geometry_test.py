#!/usr/bin/env python

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
