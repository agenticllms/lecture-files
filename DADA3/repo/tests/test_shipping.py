import unittest

from huskyutils.shipping import shipping_cost


class TestShippingCost(unittest.TestCase):
    def test_light(self):
        self.assertEqual(shipping_cost(0.4), 500)

    def test_medium(self):
        self.assertEqual(shipping_cost(3), 900)

    def test_heavy(self):
        self.assertEqual(shipping_cost(5.2), 1100)
