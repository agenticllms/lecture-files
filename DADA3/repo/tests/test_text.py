import unittest

from huskyutils.text import slugify, word_count


class TestSlugify(unittest.TestCase):
    def test_simple_title(self):
        self.assertEqual(slugify("Wireless Headphones"), "wireless-headphones")

    def test_lowercase(self):
        self.assertEqual(slugify("WEBCAM"), "webcam")


class TestWordCount(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(word_count("Great keyboard, fast shipping"), 4)

    def test_extra_spaces(self):
        self.assertEqual(word_count("  works   great  "), 2)

    def test_empty(self):
        self.assertEqual(word_count(""), 0)
