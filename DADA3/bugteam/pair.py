"""Notebook 01: the fixer and the verifier, handing one issue back and forth.

    START -> fixer --transfer_to_verifier--> verifier --accept_fix--> END
               ^                                |
               +-------transfer_to_fixer--------+      at most MAX_ROUNDS verifier runs

The verifier's reason for sending a fix back becomes the fixer's next message, so the fixer sees
the failing test and its output.
"""
import operator
from typing import Annotated, TypedDict

from langchain.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from . import config
from .fixer import build_fixer, find_fix
from .repo import issue_text
from .verifier import verify


class PairState(TypedDict):
    issue: dict
    messages: Annotated[list, add_messages]   # the fixer's conversation, kept across rounds
    fix: dict                                 # the last fix the fixer handed over
    rounds: Annotated[int, operator.add]      # how many times the verifier has run
    status: str                               # checking, verified, rejected, or no_fix
    evidence: str                             # the verifier's evidence, or its last reason
    test: str                                 # the test the verifier wrote
    log: Annotated[list, operator.add]        # the handoffs, in order


def fixer_node(state: PairState) -> dict:
    out = build_fixer().invoke({"messages": state["messages"]}, {"recursion_limit": 30})
    new = out["messages"][len(state["messages"]):]    # this round's messages only
    fix = find_fix(new)
    if fix is None:   # the last fix it handed over, if any, stays in the state for the report
        return {"messages": new, "status": "no_fix", "log": ["fixer stopped without handing over a fix"]}
    return {"messages": new, "fix": fix, "status": "checking", "log": [f"fixer -> verifier: {fix['note']}"]}


def verifier_node(state: PairState) -> dict:
    result = verify(state["issue"], state["fix"])
    if result["decision"] == "accept":
        return {"rounds": 1, "status": "verified", "evidence": result["message"], "test": result["test"],
                "log": ["verifier accepted the fix"]}
    reason = result["message"] or "The verifier stopped without accepting the fix or giving a reason."
    note = HumanMessage(content=f"The verifier sent your fix back. Its reason:\n\n{reason}\n\n"
                                "Correct the fix and hand it to the verifier again.")
    return {"rounds": 1, "status": "rejected", "evidence": reason, "test": result["test"],
            "messages": [note], "log": [f"verifier -> fixer: {reason}"]}


def after_fixer(state: PairState) -> str:
    """To the verifier if the fixer handed over a fix this time, otherwise the pair is done."""
    # TODO 1.5
    # your code here
    raise NotImplementedError


def after_verifier(state: PairState) -> str:
    """Done if the fix was verified or the rounds are used up, otherwise back to the fixer."""
    # TODO 1.5
    # your code here
    raise NotImplementedError


def build_pair():
    builder = StateGraph(PairState)
    builder.add_node("fixer", fixer_node)
    builder.add_node("verifier", verifier_node)
    builder.add_edge(START, "fixer")
    builder.add_conditional_edges("fixer", after_fixer, ["verifier", END])
    builder.add_conditional_edges("verifier", after_verifier, ["fixer", END])
    return builder.compile()


def fix_issue(issue, note="", callbacks=None):
    """Run the pair on one issue. note is what triage said about it. Returns the record the team and
    the report use. callbacks, such as a CallCounter, see every model call."""
    request = issue_text(issue) + (f"\n\nTriage: {note}" if note else "")
    out = build_pair().invoke({"issue": issue, "messages": [HumanMessage(content=request)]},
                              {"recursion_limit": 40, **({"callbacks": callbacks} if callbacks else {})})
    return {"number": issue["number"], "title": issue["title"], "status": out["status"],
            "rounds": out["rounds"], "fix": out.get("fix", {}), "evidence": out.get("evidence", ""),
            "test": out.get("test", ""), "log": out["log"]}
