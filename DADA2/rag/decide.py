"""The decision model. Nothing here is a TODO.

A chat model answers a question by writing. A decision model answers by
picking: you hand it some state and a few typed questions, and it returns a
probability for every allowed answer. No prose, no parsing, and it comes back
in well under a second.

That makes it the right tool for the two places in our graph where we need a
verdict rather than text: which strategy a question needs, and whether the
passages we found are enough. Those are decisions, not writing. The chat model
still does the writing.

Cloudflare hosts two of these, clef and clef-flash. Both speak the same API as
Jev, the model that started this category. We use clef-flash.
"""
import functools
import os

import requests

from . import config

API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}"


@functools.lru_cache(maxsize=1)
def account_id():
    """Use the one in .env, or ask Cloudflare which account the token owns."""
    if config.CF_ACCOUNT_ID:
        return config.CF_ACCOUNT_ID
    r = requests.get("https://api.cloudflare.com/client/v4/accounts",
                     headers=_headers(), timeout=30).json()
    if not r.get("result"):
        raise RuntimeError("Cloudflare returned no accounts for this token. Put "
                           "CLOUDFLARE_ACCOUNT_ID in .env.")
    return r["result"][0]["id"]


def _headers():
    if not config.CF_TOKEN:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is not set. See example.env.")
    return {"Authorization": f"Bearer {config.CF_TOKEN}"}


def decide(state, questions, model=None):
    """Ask the decision model. Returns the answers dict, keyed like questions.

    state      a string, or a dict or list. Long text is cut to fit.
    questions  {id: {"type": "choice"|"noul"|"score", "instructions": ..., "criteria": ...}}

    A choice answer looks like
        {"choice": "comparative", "probabilities": {...}, "confidence": 0.5}
    and a noul answer is just {"noul": 0.94}, the probability of yes.
    """
    model = model or config.DECISION_MODEL
    r = requests.post(API.format(account=account_id(), model=model), headers=_headers(),
                      json={"model": model, "state": state, "questions": questions},
                      timeout=60)
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(f"decision model refused: {body.get('errors')}")
    return body["result"]["answers"]


# ----------------------------------------------------------- the two we use

SCOPES = {
    "specific": "one named company and one fiscal year",
    "comparative": "two or more companies, or several years, or no company named",
    "figure": "a single reported number such as revenue or R&D spend",
}


def scope(question):
    """What kind of question is this? Returns (choice, probabilities)."""
    a = decide(question, {"scope": {
        "type": "choice",
        "instructions": "What does this question about SEC 10-K filings ask for?",
        "criteria": SCOPES}})["scope"]
    return a["choice"], a["probabilities"]


VERDICTS = {
    "sufficient": "the passages contain everything needed to answer the question",
    "absent": "the filings do not cover this topic at all; the passages are about other things",
    "wrong_words": "the filings cover this topic but these passages are about neighboring "
                   "material, not the part that answers it",
    "incomplete": "part of the question is answered by these passages and another part is not",
}


def diagnose(question, passages):
    """Do these passages answer the question, and if not, why not?

    passages is a list of (source, text). Returns (verdict, probabilities).
    """
    state = {"question": question,
             "passages": [{"source": s, "text": t[:1200]} for s, t in passages]}
    a = decide(state, {"verdict": {
        "type": "choice",
        "instructions": "Do these passages from SEC 10-K filings answer the question? "
                        "If not, why not?",
        "criteria": VERDICTS}})["verdict"]
    return a["choice"], a["probabilities"]
