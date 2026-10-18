"""The ladder agent, given. This is the agent from the first version of DADA2,
with two counters added so notebook 04 can put a bill next to each answer.

It has no decision model. The chat model grades, and a failed grade moves one
rung up a ladder of searches. Notebook 04 runs it against your agent.
"""
import operator
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field

from . import config, retrieval
from .util import retry, text_of

LADDER = ["filter", "filter+rrf", "filter+rrf+rerank"]
CHAT_CALLS = {"filter": 1, "filter+rrf": 2, "filter+rrf+rerank": 2}
MAX_ATTEMPTS = 3


def format_passages(hits):
    return "\n\n".join(f"[{source}] {text}" for source, text in hits)


class State(TypedDict, total=False):
    question: str
    rung: int
    documents: Annotated[list, operator.add]
    grade: str
    missing: str
    attempts: int
    chat_calls: Annotated[int, operator.add]
    decision_calls: Annotated[int, operator.add]
    answer: str


class Grade(BaseModel):
    """Whether the passages answer the question."""
    reasoning: str = Field(description="what the passages do and do not cover")
    sufficient: bool = Field(description="true if the question can be answered")
    missing: str = Field(default="", description="what is still needed")


def retrieve(state: State) -> dict:
    strategy = LADDER[min(state.get("rung", 0), len(LADDER) - 1)]
    hits = retrieval.STRATEGIES[strategy](state["question"], config.K)
    return {"documents": hits, "attempts": state.get("attempts", 0) + 1,
            "chat_calls": CHAT_CALLS[strategy]}


def grade(state: State) -> dict:
    grader = config.chat().with_structured_output(Grade)
    result = retry(grader.invoke, f"Question: {state['question']}\n\nPassages:\n"
                   f"{format_passages(state['documents'])}\n\nCan the question be "
                   "answered from these?")
    return {"grade": "sufficient" if result.sufficient else "insufficient",
            "missing": result.missing, "chat_calls": 1}


def escalate(state: State) -> dict:
    return {"rung": state.get("rung", 0) + 1}


def decide(state: State) -> Literal["escalate", "answer"]:
    if state["grade"] == "sufficient":
        return "answer"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        return "answer"
    if state.get("rung", 0) >= len(LADDER) - 1:
        return "answer"
    return "escalate"


ANSWER_PROMPT = """Answer the question using only these passages from SEC
filings. Cite the filing each fact comes from, by its filename in brackets.
If the passages do not support an answer, say so.

Question: {question}

Passages:
{passages}"""


def answer(state: State) -> dict:
    out = retry(config.chat().invoke, ANSWER_PROMPT.format(
        question=state["question"], passages=format_passages(state["documents"])))
    return {"answer": text_of(out), "chat_calls": 1}


def build_graph():
    from langgraph.graph import StateGraph, START, END

    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    g.add_node("grade", grade)
    g.add_node("escalate", escalate)
    g.add_node("answer", answer)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", decide)
    g.add_edge("escalate", "retrieve")
    g.add_edge("answer", END)
    return g.compile()


def run(question):
    return build_graph().invoke({"question": question, "rung": 0, "attempts": 0,
                                 "chat_calls": 0, "decision_calls": 0})


def ask(question):
    return run(question)["answer"]
