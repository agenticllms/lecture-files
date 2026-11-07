import unittest

from huskyutils.stats import median


class TestMedian(unittest.TestCase):
    def test_odd(self):
        self.assertEqual(median([3, 1, 2]), 2)

    def test_single(self):
        self.assertEqual(median([7]), 7)

    def test_does_not_modify_input(self):
        values = [3, 1, 2]
        median(values)
        self.assertEqual(values, [3, 1, 2])
