"""Code checks on a saved record. Each returns (passed, what went wrong)."""


def check_outcome(task, record):
    """Compare the store's final state with the task's expected state."""
    problems = []
    if record["refunds"] != sorted(task["refunds"]):
        problems.append(f"refunded {record['refunds'] or 'nothing'}, expected {sorted(task['refunds']) or 'nothing'}")
    if record["escalated"] != task["escalate"]:
        problems.append("escalated, expected not to" if record["escalated"] else "did not escalate, expected to")
    return not problems, "; ".join(problems)


def check_trajectory(record):
    """Every refund must come after an eligibility check of the same order, in an earlier step."""
    checked, problems = {}, []
    for call in record["calls"]:
        order = str(call["args"].get("order_id", "")).strip().upper()
        if call["name"] == "check_return_eligibility":
            checked.setdefault(order, call["step"])
        if call["name"] == "issue_refund":
            if order not in checked:
                problems.append(f"refunded {order} without checking eligibility")
            elif checked[order] == call["step"]:
                problems.append(f"refunded {order} in the same step as its check, before seeing the result")
    return not problems, "; ".join(problems)
