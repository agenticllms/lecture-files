"""Shipping prices."""
import math


def shipping_cost(weight_kg):
    """The shipping price of a package, in cents.

    - Up to and including 1 kg: $5.00
    - Over 1 kg, up to and including 5 kg: $9.00
    - Over 5 kg: $9.00 plus $2.00 for each started kilogram over 5

        shipping_cost(0.4) == 500
        shipping_cost(5.2) == 1100
    """
    if weight_kg < 1:
        return 500
    if weight_kg <= 5:
        return 900
    return 900 + 200 * math.ceil(weight_kg - 5)
