import unittest

from huskyutils.intervals import merge_intervals


class TestMergeIntervals(unittest.TestCase):
    def test_overlapping(self):
        self.assertEqual(merge_intervals([[1, 3], [2, 6], [8, 10]]), [[1, 6], [8, 10]])

    def test_touching(self):
        self.assertEqual(merge_intervals([[1, 4], [4, 5]]), [[1, 5]])

    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])

    def test_does_not_modify_input(self):
        windows = [[2, 6], [1, 3]]
        merge_intervals(windows)
        self.assertEqual(windows, [[2, 6], [1, 3]])
