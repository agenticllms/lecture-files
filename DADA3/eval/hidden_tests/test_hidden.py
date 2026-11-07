"""Held-out tests, one class per issue. The team never sees these. evaluate.py runs them in a
sandbox against the repository after your team's fixes, and against the baseline's."""
import unittest
from datetime import date


class Issue1Slugify(unittest.TestCase):
    def test_issue(self):
        from huskyutils.text import slugify
        self.assertEqual(slugify("Webcam (HD)"), "webcam-hd")
        self.assertEqual(slugify("Hello, World! T-shirt"), "hello-world-t-shirt")

    def test_docstring(self):
        from huskyutils.text import slugify
        self.assertEqual(slugify("USB-C Dock (2nd gen)"), "usb-c-dock-2nd-gen")
        self.assertEqual(slugify("  --Gaming   Laptop!!  "), "gaming-laptop")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("Crème Brûlée Mug"), "creme-brulee-mug")
        self.assertEqual(slugify("Café au lait"), "cafe-au-lait")
        self.assertEqual(slugify("Wireless Headphones"), "wireless-headphones")


class Issue2SplitAmount(unittest.TestCase):
    def test_issue(self):
        from huskyutils.money import split_amount
        self.assertEqual(sum(split_amount(1000, 3)), 1000)

    def test_docstring(self):
        from huskyutils.money import split_amount
        self.assertEqual(split_amount(1000, 3), [334, 333, 333])
        self.assertEqual(split_amount(1001, 4), [251, 250, 250, 250])
        self.assertEqual(split_amount(1002, 4), [251, 251, 250, 250])
        self.assertEqual(split_amount(900, 3), [300, 300, 300])
        self.assertEqual(split_amount(2, 5), [1, 1, 0, 0, 0])
        self.assertEqual(split_amount(-1000, 3), [-334, -333, -333])
        self.assertEqual(split_amount(-1001, 4), [-251, -250, -250, -250])


class Issue3WordCountUnchanged(unittest.TestCase):
    """Issue 3 is not a bug: the docstring says punctuation stays attached. The behavior must not change."""
    def test_unchanged(self):
        from huskyutils.text import word_count
        self.assertEqual(word_count("don't stop"), 2)
        self.assertEqual(word_count("Great keyboard, fast shipping"), 4)


class Issue4BusinessDays(unittest.TestCase):
    def test_issue(self):
        from huskyutils.dates import add_business_days
        self.assertEqual(add_business_days(date(2026, 11, 5), 3), date(2026, 11, 10))

    def test_docstring(self):
        from huskyutils.dates import add_business_days
        self.assertEqual(add_business_days(date(2026, 11, 6), 1), date(2026, 11, 9))
        self.assertEqual(add_business_days(date(2026, 11, 2), 10), date(2026, 11, 16))
        self.assertEqual(add_business_days(date(2026, 11, 7), 1), date(2026, 11, 9))    # Saturday -> Monday
        self.assertEqual(add_business_days(date(2026, 11, 8), 0), date(2026, 11, 8))    # Sunday, zero days
        self.assertEqual(add_business_days(date(2026, 11, 2), 4), date(2026, 11, 6))
        holiday = {date(2026, 11, 4)}                                                   # a Wednesday
        self.assertEqual(add_business_days(date(2026, 11, 2), 3, holidays=holiday), date(2026, 11, 6))
        self.assertEqual(add_business_days(date(2026, 11, 6), 1, holidays={date(2026, 11, 9)}), date(2026, 11, 10))


class Issue5MergeIntervals(unittest.TestCase):
    def test_issue(self):
        from huskyutils.intervals import merge_intervals
        self.assertEqual(merge_intervals([[8, 10], [1, 3], [2, 6]]), [[1, 6], [8, 10]])

    def test_docstring(self):
        from huskyutils.intervals import merge_intervals
        self.assertEqual(merge_intervals([[4, 5], [1, 4]]), [[1, 5]])
        self.assertEqual(merge_intervals([[5, 6], [1, 2], [3, 4]]), [[1, 2], [3, 4], [5, 6]])
        windows = [[8, 10], [1, 3], [2, 6]]
        merge_intervals(windows)
        self.assertEqual(windows, [[8, 10], [1, 3], [2, 6]])
        pairs = [[1, 3], [2, 6]]
        merge_intervals(pairs)
        self.assertEqual(pairs, [[1, 3], [2, 6]])


class Issue6Shipping(unittest.TestCase):
    def test_issue(self):
        from huskyutils.shipping import shipping_cost
        self.assertEqual(shipping_cost(1), 500)

    def test_docstring(self):
        from huskyutils.shipping import shipping_cost
        self.assertEqual(shipping_cost(0.4), 500)
        self.assertEqual(shipping_cost(1.01), 900)
        self.assertEqual(shipping_cost(5), 900)
        self.assertEqual(shipping_cost(5.2), 1100)
        self.assertEqual(shipping_cost(7), 1300)


class Issue7ShippingUnchanged(unittest.TestCase):
    """Issue 7 is a feature request, not a bug. shipping_cost takes a weight only and must not change."""
    def test_unchanged(self):
        from huskyutils.shipping import shipping_cost
        self.assertEqual(shipping_cost(3), 900)


class Issue9ShippingUnchanged(unittest.TestCase):
    """Issue 9 is not a bug: the docstring says up to and including 5 kg costs $9.00."""
    def test_unchanged(self):
        from huskyutils.shipping import shipping_cost
        self.assertEqual(shipping_cost(5), 900)


class Issue8Median(unittest.TestCase):
    def test_issue(self):
        from huskyutils.stats import median
        self.assertEqual(median([10, 20, 30, 40]), 25)

    def test_docstring(self):
        from huskyutils.stats import median
        self.assertEqual(median([4, 1, 3, 2]), 2.5)
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([7]), 7)
        values = [4, 1, 3, 2]
        median(values)
        self.assertEqual(values, [4, 1, 3, 2])


class Issue10Truncate(unittest.TestCase):
    def test_issue(self):
        from huskyutils.cards import truncate
        result = truncate("Wireless noise-cancelling headphones with case", 30)
        self.assertLessEqual(len(result), 30)
        self.assertTrue(result.endswith("..."))

    def test_docstring(self):
        from huskyutils.cards import truncate
        self.assertEqual(truncate("Wireless noise-cancelling headphones with case", 30), "Wireless noise-cancelling...")
        self.assertEqual(truncate("Wireless headphones", 30), "Wireless headphones")
        self.assertEqual(truncate("USB-C dock", 10), "USB-C dock")
        self.assertEqual(truncate("Mechanical keyboard with brown switches", 20), "Mechanical...")
        self.assertEqual(truncate("Mechanical keyboard with brown switches", 23), "Mechanical keyboard...")
        self.assertEqual(truncate("Supercalifragilistic headphones", 12), "Supercali...")


if __name__ == "__main__":
    unittest.main()
