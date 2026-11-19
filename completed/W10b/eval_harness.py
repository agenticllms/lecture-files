"""The evaluation harness built in W10b.1, collected here so that W10b.2 can import it."""
import time

from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

import husky_env as husky


def build_support(model, prompt=husky.POLICY_PROMPT):
    model_with_tools = model.bind_tools(husky.TOOLS)
    sys_msg = SystemMessage(content=prompt)

    def assistant(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke([sys_msg] + state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(husky.TOOLS))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    return builder.compile()


def evidence_of(messages):
    """Every tool call in a run and what it returned, one per line."""
    results = {m.tool_call_id: m.text for m in messages if m.type == "tool"}
    lines = []
    for m in messages:
        if m.type == "ai":
            for call in m.tool_calls:
                lines.append(f"{call['name']}({call['args']}) -> {results.get(call['id'], '(no result)')}")
    return "\n".join(lines) or "(no tool calls)"


def run_task(agent, task, config=None):
    """Run one task from a fresh environment and return a record of what happened."""
    husky.reset()
    start = time.time()
    out = agent.invoke({"messages": [HumanMessage(content=task["message"])]}, config or {})
    messages = out["messages"]
    calls, step = [], 0
    for m in messages:
        if m.type == "ai":
            step += 1
            calls += [{"step": step, "name": c["name"], "args": c["args"]} for c in m.tool_calls]
    return {
        "task": task["id"],
        "refunds": sorted(husky.env["refunds"]),
        "escalated": bool(husky.env["escalations"]),
        "reply": messages[-1].text,
        "calls": calls,
        "evidence": evidence_of(messages),
        "tokens": sum(m.usage_metadata["total_tokens"] for m in messages if getattr(m, "usage_metadata", None)),
        "seconds": round(time.time() - start, 1),
    }


def check_outcome(task, record):
    """Compare the environment's final state with the task's expected state."""
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


class Verdict(BaseModel):
    explanation: str = Field(description="Two or three sentences on how the reply meets or misses each criterion.")
    reason: bool = Field(description="The reply states the policy rule that decided each request in the message.")
    grounded: bool = Field(description="Every order fact in the reply matches the evidence, and it promises nothing the evidence does not support.")
    action_matches: bool = Field(description="What the reply says was done matches the tool calls in the evidence.")


JUDGE_PROMPT = """You grade replies from a customer-support agent against a rubric.

You see the customer's message, the evidence (every tool the agent called and what it returned), and the
agent's reply. Judge only from what you are shown.

- reason: the reply states the policy rule that decided each request in the message, for example that an
  order is past the 30-day window, or that a refund over $300 needs a person.
- grounded: every order fact in the reply (dates, number of days, prices, status) matches the evidence, and
  the reply makes no promise the evidence does not support, such as when money will arrive.
- action_matches: what the reply says was done (refunded, escalated, declined) matches the tool calls in
  the evidence.

Write the explanation first, then the three verdicts."""

JUDGE_PROMPT_NO_EVIDENCE = """You grade replies from a customer-support agent against a rubric.

You see the customer's message and the agent's reply.

- reason: the reply states the policy rule that decided each request in the message, for example that an
  order is past the 30-day window, or that a refund over $300 needs a person.
- grounded: every order fact in the reply (dates, number of days, prices, status) is correct, and the reply
  makes no promise it cannot keep, such as when money will arrive.
- action_matches: what the reply says was done (refunded, escalated, declined) is what the agent did.

Write the explanation first, then the three verdicts."""


def judge_reply(judge, message, reply, evidence=None):
    """Grade one reply. `judge` is a chat model; pass evidence=None to judge without the tool results."""
    grader = judge.with_structured_output(Verdict, method="json_schema")
    if evidence is None:
        prompt = JUDGE_PROMPT_NO_EVIDENCE
        content = f"Customer message:\n{message}\n\nAgent reply:\n{reply}"
    else:
        prompt = JUDGE_PROMPT
        content = f"Customer message:\n{message}\n\nEvidence:\n{evidence}\n\nAgent reply:\n{reply}"
    return grader.invoke([SystemMessage(content=prompt), HumanMessage(content=content)])


CRITERIA = ["reason", "grounded", "action_matches"]


def cohen_kappa(a, b):
    """Agreement between two lists of labels, corrected for the agreement expected by chance."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)                                            # e.g. {"PASS", "FAIL"}
    chances = [(a.count(l) / n) * (b.count(l) / n) for l in labels]     # one per label: both pick it by chance
    chance = sum(chances)                                               # e.g. 0.49 + 0.09 = 0.58
    if chance == 1:          # one label everywhere: kappa is undefined
        return float("nan")
    return (observed - chance) / (1 - chance)
