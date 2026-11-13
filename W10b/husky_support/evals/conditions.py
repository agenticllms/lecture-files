"""The experiment's conditions and data. Adding a condition is one line here, not a code change elsewhere."""
import json
from pathlib import Path

from app import store

CONDITIONS = {
    "policy": store.POLICY_PROMPT,   # the baseline
    "check": store.CHECK_PROMPT,     # the change: write the facts out before acting
}

DATA = Path(__file__).parent / "data"


def tasks():
    """The task set: each task has a customer message and the end state it should produce."""
    return json.loads((DATA / "tasks.json").read_text())


def judge_labels():
    """Replies labeled by people, for checking the judge."""
    return json.loads((DATA / "judge_labels.json").read_text())
