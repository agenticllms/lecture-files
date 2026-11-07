import unittest
from datetime import date

from huskyutils.dates import add_business_days


class TestAddBusinessDays(unittest.TestCase):
    def test_within_a_week(self):
        self.assertEqual(add_business_days(date(2026, 11, 2), 2), date(2026, 11, 4))   # Mon -> Wed

    def test_friday_plus_one(self):
        self.assertEqual(add_business_days(date(2026, 11, 6), 1), date(2026, 11, 9))   # Fri -> Mon

    def test_holiday_on_monday(self):
        self.assertEqual(add_business_days(date(2026, 11, 6), 1, holidays={date(2026, 11, 9)}),
                         date(2026, 11, 10))

    def test_zero_days(self):
        self.assertEqual(add_business_days(date(2026, 11, 7), 0), date(2026, 11, 7))
