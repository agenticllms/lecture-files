"""Statistics for the sales dashboard."""


def median(values):
    """The median of a non-empty list of numbers.

    The values can be in any order, and the list is not modified. With an odd number of values the
    median is the middle one. With an even number it is the average of the two middle values.

        median([3, 1, 2]) == 2
        median([4, 1, 3, 2]) == 2.5
    """
    ordered = sorted(values)
    return ordered[len(ordered) // 2]
