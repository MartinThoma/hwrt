"""Tools for partitioning sets."""

# http://codereview.stackexchange.com/questions/1526/finding-all-k-subset-partitions
# http://stackoverflow.com/questions/18353280/iterator-over-all-partitions-into-k-groups
# https://docs.python.org/3/library/itertools.html
# http://stackoverflow.com/questions/9316436/how-many-different-partitions-with-exactly-n-parts-can-be-made-of-a-set-with-k-e
# https://en.wikipedia.org/wiki/Partition_of_a_set
# http://math.stackexchange.com/questions/1215983/how-can-i-get-the-maximum-score-without-iterating-all-possibilities

# Core Library modules
import logging

logger = logging.getLogger(__name__)


def prepare_table(table):
    """
    Make the table 'symmetric'.

    The lower left part of the matrix is the reverse probability.
    """
    n = len(table)
    for i, row in enumerate(table):
        assert len(row) == n, f"len(row) = {len(row)} != {n} = n"
        for j, _ in enumerate(row):
            if i == j:
                table[i][i] = 0.0
            elif i > j:
                table[i][j] = 1 - table[j][i]
    return table


def clusters(l, K):  # noqa
    """
    Partition list ``l`` in ``K`` partitions.

    Examples
    --------
    >>> l = [0, 1, 2]
    >>> list(clusters(l, K=3))
    [[[0], [1], [2]], [[], [0, 1], [2]], [[], [1], [0, 2]], [[0], [], [1, 2]], [[], [0], [1, 2]], [[], [], [0, 1, 2]]]
    >>> list(clusters(l, K=2))
    [[[0, 1], [2]], [[1], [0, 2]], [[0], [1, 2]], [[], [0, 1, 2]]]
    >>> list(clusters(l, K=1))
    [[[0, 1, 2]]]
    """
    if l:
        prev = None
        for t in clusters(l[1:], K):
            tup = sorted(t)
            if tup != prev:
                prev = tup
                for i in range(K):
                    yield tup[:i] + [
                        [l[0]] + tup[i],
                    ] + tup[i + 1 :]
    else:
        yield [[] for _ in range(K)]


def neclusters(l, K):  # noqa
    """Partition list ``l`` in ``K`` partitions, without empty parts.

    >>> l = [0, 1, 2]
    >>> list(neclusters(l, 2))
    [[[0, 1], [2]], [[1], [0, 2]], [[0], [1, 2]]]
    >>> list(neclusters(l, 1))
    [[[0, 1, 2]]]
    """
    for c in clusters(l, K):
        if all(x for x in c):
            yield c


def all_segmentations(l):
    """Get all segmentations of a list ``l``.

    This gets bigger fast. See https://oeis.org/A000110
    For len(l) = 14 it is 190,899,322

    >>> list(all_segmentations([0, 1, 2]))
    [[[0, 1, 2]], [[0, 1], [2]], [[1], [0, 2]], [[0], [1, 2]], [[0], [1], [2]]]

    """
    for K in range(1, len(l) + 1):
        gen = neclusters(l, K)
        yield from gen


def find_index(segmentation, stroke_id):
    """
    >>> find_index([[0, 1, 2], [3, 4], [5, 6, 7]], 0)
    0
    >>> find_index([[0, 1, 2], [3, 4], [5, 6, 7]], 1)
    0
    >>> find_index([[0, 1, 2], [3, 4], [5, 6, 7]], 5)
    2
    >>> find_index([[0, 1, 2], [3, 4], [5, 6, 7]], 6)
    2
    """
    for i, symbol in enumerate(segmentation):
        for sid in symbol:
            if sid == stroke_id:
                return i
    return -1


def q(segmentation, s1, s2):
    """Test if ``s1`` and ``s2`` are in the same symbol, given the
    ``segmentation``.
    """
    index1 = find_index(segmentation, s1)
    index2 = find_index(segmentation, s2)
    return index1 == index2


class TopFinder:
    """Utility datastructure to find the top n elements."""

    def __init__(self, n, find_min=False):
        self.n = n
        self.tops = []
        self.find_min = find_min

    def push(self, element, value):
        """Push an ``element`` into the datastrucutre together with its value
        and only save it if it currently is one of the top n elements.

        Drop elements if necessary.
        """
        insert_pos = 0
        for index, el in enumerate(self.tops):
            if not self.find_min and el[1] >= value:
                insert_pos = index + 1
            elif self.find_min and el[1] <= value:
                insert_pos = index + 1
        self.tops.insert(insert_pos, [element, value])
        self.tops = self.tops[: self.n]

    def __iter__(self):
        return self.tops.__iter__()


def score_segmentation(segmentation, table):
    """Get the score of a segmentation."""
    stroke_nr = sum(1 for symbol in segmentation for stroke in symbol)
    score = 1
    for i in range(stroke_nr):
        for j in range(i + 1, stroke_nr):
            qval = q(segmentation, i, j)
            if qval:
                score *= table[i][j]
            else:
                score *= table[j][i]
    return score


def normalize_segmentation(segmentation):
    for i in range(len(segmentation)):
        segmentation[i] = sorted(segmentation[i])
    return sorted(segmentation, key=lambda x: x[0])


def get_top_segmentations(table, n):
    """
    Parameters
    ----------
    table : matrix of probabilities
        Each cell (i, j) of `table` gives the probability that i and j are in
        the same symbol.
    n : int
        Number of best segmentations which get returned
    """
    stroke_count = list(range(len(table)))
    topf = TopFinder(n)
    for curr_segmentation in all_segmentations(stroke_count):
        curr_seg_score = score_segmentation(curr_segmentation, table)
        topf.push(curr_segmentation, curr_seg_score)

    for el, score in topf:
        yield [normalize_segmentation(el), score]


def main():
    # Column0     1     2     3     4     5     6     7
    table = [
        [0.00, 0.55, 0.43, 0.30, 0.28, 0.74, 0.28, 0.26],  # 0
        [0.45, 0.00, 0.67, 0.40, 0.35, 0.77, 0.30, 0.31],  # 1
        [0.57, 0.33, 0.00, 0.29, 0.28, 0.80, 0.21, 0.23],  # 2
        [0.70, 0.60, 0.71, 0.00, 0.39, 0.76, 0.29, 0.29],  # 3
        [0.72, 0.65, 0.72, 0.61, 0.00, 0.76, 0.25, 0.29],  # 4
        [0.26, 0.23, 0.20, 0.24, 0.24, 0.00, 0.30, 0.31],  # 5
        [0.72, 0.70, 0.19, 0.71, 0.75, 0.70, 0.00, 0.27],  # 6
        [0.74, 0.69, 0.77, 0.71, 0.71, 0.69, 0.73, 0.00],
    ]  # 7
    #            0     1     2
    # table = [[0.00, 0.01, 0.99],
    #          [0.99, 0.00, 0.01],  # noqa
    #          [0.01, 0.99, 0.00]]
    topfs = get_top_segmentations(table, 5)
    for el, score in topfs:
        print(f"{score:0.10f}: {el}")
    for i in range(20):
        logger.info(f"{i:>5}: {len(list(all_segmentations(list(range(i))))):>10}")
