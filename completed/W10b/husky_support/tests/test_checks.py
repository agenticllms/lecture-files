"""Tests for the checks. A check is code, and code has bugs: run these whenever a check changes.

    python -m pytest tests
"""
from evals.checks import check_outcome, check_trajectory
from evals.metrics import cohen_kappa

TASK = {"id": "t08", "refunds": ["HT-2001", "HT-2008"], "escalate": False}


def record(refunds=(), escalated=False, calls=()):
    return {"refunds": sorted(refunds), "escalated": escalated, "calls": list(calls)}


def call(step, name, order_id):
    return {"step": step, "name": name, "args": {"order_id": order_id}}


def test_outcome_passes_in_any_order():
    assert check_outcome(TASK, record(refunds=["HT-2008", "HT-2001"]))[0]


def test_outcome_fails_on_a_missing_refund_and_says_why():
    ok, problem = check_outcome(TASK, record(refunds=["HT-2001"]))
    assert not ok and "expected" in problem


def test_outcome_fails_on_an_unexpected_escalation():
    assert not check_outcome(TASK, record(refunds=["HT-2001", "HT-2008"], escalated=True))[0]


def test_trajectory_passes_when_the_check_comes_first():
    calls = [call(1, "check_return_eligibility", "HT-2001"), call(2, "issue_refund", "HT-2001")]
    assert check_trajectory(record(calls=calls))[0]


def test_trajectory_normalizes_order_ids():
    calls = [call(1, "check_return_eligibility", "ht-2001 "), call(2, "issue_refund", "HT-2001")]
    assert check_trajectory(record(calls=calls))[0]


def test_trajectory_fails_without_a_check():
    assert not check_trajectory(record(calls=[call(1, "issue_refund", "HT-2001")]))[0]


def test_trajectory_fails_when_the_refund_is_in_the_same_step_as_the_check():
    calls = [call(1, "check_return_eligibility", "HT-2001"), call(1, "issue_refund", "HT-2001")]
    assert not check_trajectory(record(calls=calls))[0]


def test_kappa_is_zero_for_a_judge_that_always_says_yes():
    people = [True] * 16 + [False] * 2
    assert abs(cohen_kappa(people, [True] * 18)) < 1e-9
