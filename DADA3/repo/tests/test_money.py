import unittest

from huskyutils.money import split_amount


class TestSplitAmount(unittest.TestCase):
    def test_even_split(self):
        self.assertEqual(split_amount(900, 3), [300, 300, 300])

    def test_one_person(self):
        self.assertEqual(split_amount(1999, 1), [1999])

    def test_even_refund(self):
        self.assertEqual(split_amount(-900, 3), [-300, -300, -300])
