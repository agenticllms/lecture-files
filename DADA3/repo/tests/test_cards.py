import unittest

from huskyutils.cards import truncate


class TestTruncate(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(truncate("Wireless headphones", 30), "Wireless headphones")

    def test_exact_length_unchanged(self):
        self.assertEqual(truncate("USB-C dock", 10), "USB-C dock")

    def test_long_text_ends_with_ellipsis(self):
        self.assertTrue(truncate("Mechanical keyboard with brown switches", 20).endswith("..."))
