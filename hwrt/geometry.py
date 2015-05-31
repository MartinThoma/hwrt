#!/usr/bin/env python

"""Calculate the distance between line segments."""

import logging
import math
import itertools


class Point(object):
    """A two dimensional point."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def dist_to(self, p2):
        """Measure the distance to another point."""
        return math.hypot(self.x - p2.x, self.y - p2.y)

    def __eq__(self, other):
        return (self.x-other.x)**2 + (self.y-other.y)**2 < 0.000001

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return "p(%0.2f, %0.2f)" % (self.x, self.y)

    def __str__(self):
        return repr(self)


class LineSegment(object):
    """A line segment in a two dimensional space."""
    def __init__(self, p1, p2):
        assert isinstance(p1, Point), \
            "p1 is not of type Point, but of %r" % type(p1)
        assert isinstance(p2, Point), \
            "p2 is not of type Point, but of %r" % type(p2)
        self.p1 = p1
        self.p2 = p2

    def dist_to(self, l2):
        """Measure the distance to another line segment."""
        return segments_distance(self, l2)

    def get_slope(self):
        """Return the slope m of this line segment."""
        # y1 = m*x1 + t
        # y2 = m*x2 + t => y1-y2 = m*(x1-x2) <=> m = (y1-y2)/(x1-x2)
        return ((self.p1.y-self.p2.y) / (self.p1.x-self.p2.x))

    def get_offset(self):
        """Get the offset t of this line segment."""
        return self.p1.y-self.get_slope()*self.p1.x

    def __repr__(self):
        return "line[%s -> %s]" % (str(self.p1), str(self.p2))

    def __str__(self):
        return repr(self)


class PolygonalChain(object):
    """A list of line segments."""
    def __init__(self, pointlist):
        assert isinstance(pointlist, list), \
            "lineSegments is not of type list, but of %r" % type(pointlist)
        self.lineSegments = []
        for point1, point2 in zip(pointlist, pointlist[1:]):
            point1 = Point(point1['x'], point1['y'])
            point2 = Point(point2['x'], point2['y'])
            self.lineSegments.append(LineSegment(point1, point2))

    def __getitem__(self, key):
        return self.lineSegments[key]

    def __iter__(self):
        return iter(self.lineSegments)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str("PolygonalChain[%s]" % self.lineSegments)

    def __repr__(self):
        return repr("PolygonalChain[%s]" % self.lineSegments)

    def count_selfintersections(self):
        """ Get the number of self-intersections of this polygonal chain."""
        # This can be solved more efficiently with sweep line
        counter = 0
        for i, j in itertools.combinations(range(len(self.lineSegments)), 2):
            inters = get_segments_intersections(self.lineSegments[i],
                                                self.lineSegments[j])
            if abs(i-j) > 1 and len(inters) > 0:
                counter += 1
        return counter

    def count_intersections(self, lineSegmentsB):
        """Count the intersections of two strokes with each other."""
        lineSegmentsA = self.lineSegments

        # Calculate intersections
        intersection_points = []
        for line1, line2 in itertools.product(lineSegmentsA, lineSegmentsB):
            intersection_points += get_segments_intersections(line1, line2)
        return len(set(intersection_points))


class BoundingBox(object):
    """A rectangle whichs sides are in parallel to the axes."""
    def __init__(self, p1, p2):
        assert isinstance(p1, Point), \
            "p1 is not of type Point, but of %r" % type(p1)
        assert isinstance(p2, Point), \
            "p2 is not of type Point, but of %r" % type(p2)
        assert p1.x <= p2.x, "p1.x <= p2.x (%0.2f and %0.2f)" % (p1.x, p2.x)
        assert p1.y <= p2.y, "p1.y <= p2.y (%0.2f and %0.2f)" % (p1.y, p2.y)
        self.p1 = p1
        self.p2 = p2

    def __repr__(self):
        return "BoundingBox[%s, %s]" % (str(self.p1), str(self.p2))

    def __str__(self):
        return repr(self)

    def get_area(self):
        """Calculate area of bounding box."""
        return (self.p2.x-self.p1.x)*(self.p2.y-self.p1.y)

    def get_width(self):
        """
        >>> BoundingBox(Point(0,0), Point(3,2)).get_width()
        3.0
        """
        return self.p2.x - self.p1.x

    def get_height(self):
        """
        >>> BoundingBox(Point(0,0), Point(3,2)).get_height()
        2.0
        """
        return self.p2.y - self.p1.y

    def get_center(self):
        """
        Get the center point of this bounding box.
        """
        return Point((self.p1.x+self.p2.x)/2.0, (self.p1.y+self.p2.y)/2.0)

    def get_largest_dimension(self):
        """Get the larger dimension of the bounding box."""
        return max(self.get_height(), self.get_width())

    def grow(self, percent=0.05):
        width = (self.p2.x-self.p1.x)*percent
        height = (self.p2.y-self.p1.y)*percent
        self.p1.x -= width/2.0
        self.p2.x += width/2.0
        self.p1.y -= height/2.0
        self.p2.y += height/2.0
        return self


def get_bounding_box(points):
    """Get the bounding box of a list of points.

    Parameters
    ----------
    points : list of points

    Returns
    -------
    BoundingBox
    """
    assert len(points) > 0, "At least one point has to be given."
    min_x, max_x = points[0]['x'], points[0]['x']
    min_y, max_y = points[0]['y'], points[0]['y']
    for point in points:
        min_x, max_x = min(min_x, point['x']), max(max_x, point['x'])
        min_y, max_y = min(min_y, point['y']), max(max_y, point['y'])
    p1 = Point(min_x, min_y)
    p2 = Point(max_x, max_y)
    return BoundingBox(p1, p2)


def do_bb_intersect(a, b):
    """Check if BoundingBox a intersects with BoundingBox b."""
    return a.p1.x <= b.p2.x \
        and a.p2.x >= b.p1.x \
        and a.p1.y <= b.p2.y \
        and a.p2.y >= b.p1.y


def segments_distance(segment1, segment2):
    """Calculate the distance between two line segments in the plane.

    >>> a = LineSegment(Point(1,0), Point(2,0))
    >>> b = LineSegment(Point(0,1), Point(0,2))
    >>> "%0.2f" % segments_distance(a, b)
    '1.41'
    >>> c = LineSegment(Point(0,0), Point(5,5))
    >>> d = LineSegment(Point(2,2), Point(4,4))
    >>> e = LineSegment(Point(2,2), Point(7,7))
    >>> "%0.2f" % segments_distance(c, d)
    '0.00'
    >>> "%0.2f" % segments_distance(c, e)
    '0.00'
    """
    assert isinstance(segment1, LineSegment), \
        "segment1 is not a LineSegment, but a %s" % type(segment1)
    assert isinstance(segment2, LineSegment), \
        "segment2 is not a LineSegment, but a %s" % type(segment2)
    if len(get_segments_intersections(segment1, segment2)) >= 1:
        return 0
    # try each of the 4 vertices w/the other segment
    distances = []
    distances.append(point_segment_distance(segment1.p1, segment2))
    distances.append(point_segment_distance(segment1.p2, segment2))
    distances.append(point_segment_distance(segment2.p1, segment1))
    distances.append(point_segment_distance(segment2.p2, segment1))
    return min(distances)


def get_segments_intersections(segment1, segment2):
    """Return at least one point in a list where segments intersect if an
       intersection exists. Otherwise, return an empty list.
    >>> get_segments_intersections(LineSegment(Point(0,0), Point(1,0)), \
                                   LineSegment(Point(0,0), Point(1,0)))
    [Point(0,0)]
    """
    dx1 = segment1.p2.x - segment1.p1.x
    dy1 = segment1.p2.y - segment1.p1.y
    dx2 = segment2.p2.x - segment2.p1.x
    dy2 = segment2.p2.y - segment2.p1.y
    delta = dx2 * dy1 - dy2 * dx1
    if delta == 0:  # parallel segments
        # Line segments could be (partially) identical.
        # In that case this functin should return True.
        if dx1 == 0 and dy1 == 0:  # segment1 is a point
            point = segment1.p1
            if segment2.p1.x == point.x and segment2.p1.y == point.y:
                return [Point(point.x, point.y)]
            elif segment2.p2.x == point.x and segment2.p2.y == point.y:
                return [Point(point.x, point.y)]
            else:
                return []
        elif dx2 == 0 and dy2 == 0:  # segment2 is a point
            point = segment2.p1
            if segment1.p1.x == point.x and segment1.p1.y == point.y:
                return [Point(point.x, point.y)]
            elif segment1.p2.x == point.x and segment1.p2.y == point.y:
                return [Point(point.x, point.y)]
            else:
                return []
        elif dx1 == 0:
            # Lines segments are vertical
            if segment1.p1.x == segment2.p1.x:
                if segment1.p1.y > segment1.p2.y:
                    segment1.p1, segment1.p2 = segment1.p2, segment1.p1
                if segment2.p1.y > segment2.p2.y:
                    segment2.p1, segment2.p2 = segment2.p2, segment2.p1
                # Lines segments are on the same line
                if segment1.p1.y <= segment2.p1.y <= segment1.p2.y:
                    return [Point(segment1.p1.x, segment2.p1.y)]
                if segment2.p1.y <= segment1.p1.y <= segment2.p2.y:
                    return [Point(segment1.p1.x, segment1.p1.y)]
        else:
            # The equation f(x) = m*x + t defines any non-vertical line
            t1 = segment1.get_offset()
            t2 = segment2.get_offset()
            if t1 == t2:  # line segments are on the same line
                if segment1.p1.x <= segment2.p1.x <= segment1.p2.x:
                    return [Point(segment2.p1.x,
                                  segment2.get_slope()*segment2.p1.x+t2)]
                if segment2.p1.x <= segment1.p1.x <= segment2.p2.x:
                    return [Point(segment1.p1.x,
                                  segment1.get_slope()*segment1.p1.x+t1)]
        return []
    if dx2 == 0:  # Line 2 is a vertical line, but line 1 isn't
        segment1, segment2 = segment2, segment1
        dx1, dx2 = dx2, dx1
    if dx1 == 0:  # Line 1 is a vertical line, but line 2 isn't
        if segment2.p1.x > segment2.p2.x:
            segment2.p1, segment2.p2 = segment2.p2, segment2.p1
        if segment2.p1.x <= segment1.p1.x <= segment2.p2.x:
            # The x-values overlap
            m2 = segment2.get_slope()
            t2 = segment2.get_offset()
            y = m2*segment1.p1.x + t2
            if segment1.p1.y > segment1.p2.y:
                segment1.p1, segment1.p2 = segment1.p2, segment1.p1
            if segment1.p1.y <= y <= segment1.p2.y:
                return [Point(segment1.p1.x, y)]
            else:
                return []
        else:
            return []

    m1, t1 = segment1.get_slope(), segment1.get_offset()
    m2, t2 = segment2.get_slope(), segment2.get_offset()
    try:
        x = (t2-t1)/(m1-m2)
    except Exception as inst:
        logging.debug(inst)
        logging.debug("m1=%s", repr(m1))
        logging.debug("m2=%s", repr(m2))
        return []
    if segment1.p1.x > segment1.p2.x:
        segment1.p1, segment1.p2 = segment1.p2, segment1.p1
    if segment2.p1.x > segment2.p2.x:
        segment2.p1, segment2.p2 = segment2.p2, segment2.p1
    if (segment1.p1.x <= x <= segment1.p2.x) and \
       (segment2.p1.x <= x <= segment2.p2.x):
        # The intersection is on both line segments - not only on the lines
        return [Point(x, m1*x+t1)]
    else:
        return []


def point_segment_distance(point, segment):
    """
    >>> a = LineSegment(Point(1,0), Point(2,0))
    >>> b = LineSegment(Point(2,0), Point(0,2))
    >>> point_segment_distance(Point(0,0), a)
    1.0
    >>> "%0.2f" % point_segment_distance(Point(0,0), b)
    '1.41'
    """
    assert isinstance(point, Point), \
        "point is not of type Point, but of %r" % type(point)
    dx = segment.p2.x - segment.p1.x
    dy = segment.p2.y - segment.p1.y
    if dx == dy == 0:  # the segment's just a point
        return point.dist_to(segment.p1)

    if dx == 0:  # It's a straight vertical line
        pIsBelowP1 = point.y <= segment.p1.y and segment.p1.y <= segment.p2.y
        pIsBelowP2 = point.y <= segment.p2.y and segment.p2.y <= segment.p1.y
        pIsAboveP2 = segment.p1.y <= segment.p2.y and segment.p2.y <= point.y
        pIsAboveP1 = segment.p2.y <= segment.p1.y and segment.p1.y <= point.y
        if pIsBelowP1 or pIsAboveP1:
            return point.dist_to(segment.p1)
        elif pIsBelowP2 or pIsAboveP2:
            return point.dist_to(segment.p2)

    if dy == 0:  # It's a straight horizontal line
        pIsLeftP1 = point.x <= segment.p1.x and segment.p1.x <= segment.p2.x
        pIsLeftP2 = point.x <= segment.p2.x and segment.p2.x <= segment.p1.x
        pIsRightP2 = segment.p1.x <= segment.p2.x and segment.p2.x <= point.x
        pIsRightP1 = segment.p2.x <= segment.p1.x and segment.p1.x <= point.x
        if pIsLeftP1 or pIsRightP1:
            return point.dist_to(segment.p1)
        elif pIsLeftP2 or pIsRightP2:
            return point.dist_to(segment.p2)

    # Calculate the t that minimizes the distance.
    t = ((point.x - segment.p1.x) * dx + (point.y - segment.p1.y) * dy) / \
        (dx * dx + dy * dy)

    # See if this represents one of the segment's
    # end points or a point in the middle.
    if t < 0:
        dx = point.x - segment.p1.x
        dy = point.y - segment.p1.y
    elif t > 1:
        dx = point.x - segment.p2.x
        dy = point.y - segment.p2.y
    else:
        near_x = segment.p1.x + t * dx
        near_y = segment.p1.y + t * dy
        dx = point.x - near_x
        dy = point.y - near_y
    return math.hypot(dx, dy)


def perpendicular_distance(p3, p1, p2):
    """
    Calculate the distance from p3 to the stroke defined by p1 and p2.
    The distance is the length of the perpendicular from p3 on p1.

    Parameters
    ----------
    p1 : dictionary with "x" and "y"
        start of stroke
    p2 : dictionary with "x" and "y"
        end of stroke
    p3 : dictionary with "x" and "y"
        point
    """
    px = p2['x']-p1['x']
    py = p2['y']-p1['y']

    squared_distance = px*px + py*py
    if squared_distance == 0:
        # The line is in fact only a single dot.
        # In this case the distance of two points has to be
        # calculated
        linePoint = Point(p1['x'], p1['y'])
        point = Point(p3['x'], p3['y'])
        return linePoint.dist_to(point)

    u = ((p3['x'] - p1['x'])*px + (p3['y'] - p1['y'])*py) / squared_distance

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = p1['x'] + u * px
    y = p1['y'] + u * py

    dx = x - p3['x']
    dy = y - p3['y']

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    dist = math.sqrt(dx*dx + dy*dy)
    return dist


if __name__ == '__main__':
    import doctest
    doctest.testmod()
