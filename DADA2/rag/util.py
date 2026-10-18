"""Small helpers that keep the free tier from ending your evening."""
import time


def retry(fn, *args, tries=8, base=15, **kwargs):
    """Call fn, and when the API says you are over the rate limit, wait and
    try again. Every model call in this assignment should go through here.

        order = retry(ranker.invoke, prompt)

    The free tier has two separate limits and they need opposite responses.
    The per-minute one (15) clears by itself, so we wait it out. The per-day
    one (500) does not clear until tomorrow, so backing off eight times just
    wastes nine minutes before failing anyway. We tell them apart and say
    which one you hit.
    """
    for attempt in range(tries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            message = str(e)
            over_limit = "RESOURCE_EXHAUSTED" in message or "429" in message
            if not over_limit:
                raise
            if "PerDay" in message:
                raise RuntimeError(
                    "You have used the 500 requests a day on the Gemini free "
                    "tier. Waiting will not help; this resets tomorrow. Score "
                    "fewer questions, or a few strategies at a time."
                ) from e
            time.sleep(base * (attempt + 1))
    raise RuntimeError(
        f"Still rate limited after {tries} attempts. This is the 15-a-minute "
        "limit and it should have cleared, so something else is also calling "
        "the API, or the daily limit is nearly gone too."
    )


def text_of(message):
    """The text of a model reply.

    Newer Gemini models return .content as a list of content blocks rather
    than a string, so anything that treats .content as text breaks on them.
    Everything in this assignment that reads a reply goes through here.
    """
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)
