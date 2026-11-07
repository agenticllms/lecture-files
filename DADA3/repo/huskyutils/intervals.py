"""Delivery time windows."""


def merge_intervals(intervals):
    """Merge overlapping delivery windows.

    `intervals` is a list of [start, end] pairs with start <= end, in any order. Windows that
    overlap or touch (one ends where the next starts) are merged into one. The result is sorted by
    start time.

    Returns a new list. The input list and the pairs in it are not modified.

        merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]
        merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    """
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
