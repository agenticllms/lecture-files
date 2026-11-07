"""Order and delivery dates."""
from datetime import timedelta


def add_business_days(start, days, holidays=()):
    """The date `days` business days after `start`.

    Business days are Monday to Friday, except the dates in `holidays`. Saturdays, Sundays, and
    holidays are skipped. `days` is zero or more. With days == 0 the result is `start` itself, even
    if `start` is not a business day. Otherwise the result is always a business day.

        # 2026-11-06 is a Friday
        add_business_days(date(2026, 11, 6), 1) == date(2026, 11, 9)                             # Monday
        add_business_days(date(2026, 11, 6), 1, holidays={date(2026, 11, 9)}) == date(2026, 11, 10)
    """
    if days == 0:
        return start
    result = start + timedelta(days=days)
    while result.weekday() >= 5 or result in holidays:
        result += timedelta(days=1)
    return result
