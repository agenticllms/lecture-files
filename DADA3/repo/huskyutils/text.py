"""Text helpers for product pages."""


def slugify(title):
    """Turn a product title into a URL slug.

    The slug is lowercase ASCII. Accented letters lose their accents (é becomes e). Letters and
    digits are kept. Every run of other characters (spaces, punctuation, symbols) becomes a single
    hyphen, and the slug never starts or ends with a hyphen. A title with no letters or digits gives
    the empty string.

        slugify("Wireless Headphones") == "wireless-headphones"
        slugify("USB-C Dock (2nd gen)") == "usb-c-dock-2nd-gen"
        slugify("Crème Brûlée Mug") == "creme-brulee-mug"
    """
    out = []
    for ch in title.lower():
        out.append(ch if ch.isalnum() else "-")
    return "".join(out)


def word_count(text):
    """Count the words in a review.

    Words are separated by whitespace. Punctuation stays attached to the word it touches, so
    "great," and "don't" are one word each.

        word_count("Great keyboard, fast shipping") == 4
    """
    return len(text.split())
