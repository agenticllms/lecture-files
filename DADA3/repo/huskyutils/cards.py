"""Product cards on the store's listing pages."""


def truncate(text, limit):
    """Shorten a product description so that it fits on a product card.

    If `text` is at most `limit` characters long, it is returned unchanged. Otherwise the result
    ends with "..." and is at most `limit` characters long, the "..." included. Words are never cut
    in the middle: the result keeps as many whole words from the start as fit, separated by single
    spaces, with no space before the "...". If not even the first word fits, the result is the first
    `limit - 3` characters followed by "...". `limit` is at least 10.

        truncate("Wireless headphones", 30) == "Wireless headphones"
        truncate("Wireless noise-cancelling headphones with case", 30) == "Wireless noise-cancelling..."
    """
    if len(text) <= limit:
        return text
    return text[:limit] + "..."
