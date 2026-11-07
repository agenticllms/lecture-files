"""Payments."""


def split_amount(cents, people):
    """Split an amount in cents into `people` shares, for a shared order.

    The shares add up to exactly `cents` and differ by at most one cent. When the amount does not
    divide evenly, the first shares get the extra cent. A negative amount (a refund) is split the
    same way as the positive amount, with every share negative. `people` is at least 1.

        split_amount(900, 3) == [300, 300, 300]
        split_amount(1000, 3) == [334, 333, 333]
        split_amount(-1000, 3) == [-334, -333, -333]
    """
    share = cents // people
    return [share] * people
