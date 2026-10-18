"""Notebook 03: the agent. A decision model routes and judges, a chat model writes.

Notebook 03 walks through this. Write there first, then move it in here;
app.py and notebook 04 import from this file.

    route (decision) -+-> lookup (figure questions, the financials file) -> answer
                      +-> retrieve -> diagnose (decision) -> decide
                                                             |-- sufficient / absent -> answer (chat)
                                                             |-- wrong_words        -> stronger search, back to retrieve
                                                             |-- incomplete         -> plan (chat), execute, back to diagnose
"""
import json
import operator
import os
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field

from . import config, decide as decision, retrieval
from .util import retry, text_of

MAX_ATTEMPTS = 3

# What each kind of question starts with. Measured in notebook 04 of the
# ladder version: the filter wins on specific questions and loses on
# comparative ones, where hybrid wins.
START_WITH = {"specific": "filter", "comparative": "hybrid+rrf", "figure": "filter"}
DEFAULT = "filter+rrf"            # when the router is not sure
SURE = 0.6                        # below this, use DEFAULT

# wrong_words means the search was aimed right and missed, so search harder.
STRONGER = {"filter": "filter+rrf", "hybrid+rrf": "filter+rrf+rerank",
            "filter+rrf": "filter+rrf+rerank"}

# absent is a judgment, and the model can be unsure of it. Below this we
# give it one more search before taking its word.
ABSENT_SURE = 0.8


# ---------------------------------------------------------------- the tools

def financial_fact(ticker: str, concept: str) -> str:
    """Look up a reported figure. ticker is NVDA, AMD or MU. concept is an
    XBRL name such as Revenues or ResearchAndDevelopmentExpense."""
    path = os.path.join(config.FINANCIALS, f"{ticker.upper()}_financials.json")
    if not os.path.exists(path):
        return f"No financials for {ticker}. Use NVDA, AMD or MU."
    facts = json.load(open(path))["facts"]
    if concept not in facts:
        return (f"{ticker} has no concept named {concept}. Available: "
                + ", ".join(sorted(facts)[:25]))
    rows = sorted(facts[concept].items())
    return f"{ticker} {concept}:\n" + "\n".join(
        f"  period ending {d}: {v:,}" for d, v in rows)


def format_passages(hits):
    return "\n\n".join(f"[{source}] {text}" for source, text in hits)


# ---------------------------------------------------------------- the state

class RetrievalState(TypedDict, total=False):
    question: str
    scope: str                 # specific, comparative, figure
    strategy: str              # which retrieval to run next
    documents: Annotated[list, operator.add]
    verdict: str               # sufficient, absent, wrong_words, incomplete
    probabilities: dict
    steps: list
    attempts: int
    chat_calls: Annotated[int, operator.add]
    decision_calls: Annotated[int, operator.add]
    answer: str


# ---------------------------------------------------------------- the nodes

def route(state: RetrievalState) -> dict:
    """One decision-model call. Which kind of question, and so which search.

    TODO 3.1 (1 pt), with after_route.

    decide.scope gives you a choice and its probabilities. Use START_WITH for
    the choice, unless the model is not sure, in which case use DEFAULT. SURE
    is the line. Count the call: return decision_calls as 1.
    """
    # TODO 3.1
    # your code here
    raise NotImplementedError

def after_route(state: RetrievalState) -> Literal["lookup", "retrieve"]:
    """Figure questions do not go to retrieval at all."""
    # TODO 3.1
    # your code here
    raise NotImplementedError

class Fact(BaseModel):
    """Which figure a question asks for."""
    ticker: Literal["NVDA", "AMD", "MU"]
    concept: Literal["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                     "ResearchAndDevelopmentExpense", "GrossProfit", "NetIncomeLoss",
                     "OperatingIncomeLoss"] = Field(
        description="the XBRL concept. Revenue questions: Revenues, or "
                    "RevenueFromContractWithCustomerExcludingAssessedTax for AMD. "
                    "R&D spend: ResearchAndDevelopmentExpense.")


FACT_PROMPT = """Which reported figure does this question ask for?

  research and development spend  -> ResearchAndDevelopmentExpense
  revenue, sales, top line         -> Revenues (AMD reports it as
                                      RevenueFromContractWithCustomerExcludingAssessedTax)
  gross profit, gross margin       -> GrossProfit
  net income, profit, earnings     -> NetIncomeLoss
  operating income                 -> OperatingIncomeLoss

ticker is the company's symbol: NVIDIA -> NVDA, AMD -> AMD, Micron -> MU.

Example: "What did Micron spend on R&D in fiscal 2025?"
         -> ticker=MU, concept=ResearchAndDevelopmentExpense

Question: {question}"""


def lookup(state: RetrievalState) -> dict:
    """A number is in the financials file, not in the prose. One chat call
    to name the figure, then a plain dictionary lookup.

    TODO 3.2 (1 pt)

    Ask the chat model for a Fact, call financial_fact with it, and return the
    table as the one document, with the verdict already sufficient so the
    graph goes straight to answer. attempts 1, chat_calls 1.
    """
    # TODO 3.2
    # your code here
    raise NotImplementedError

def retrieve(state: RetrievalState) -> dict:
    search = retrieval.STRATEGIES[state["strategy"]]
    hits = search(state["question"], config.K)
    seen = set(state.get("documents") or [])
    new = [h for h in hits if h not in seen]
    chat = {"filter": 1, "hybrid+rrf": 1, "filter+rrf": 2, "filter+rrf+rerank": 2}
    return {"documents": new, "attempts": state.get("attempts", 0) + 1,
            "chat_calls": chat[state["strategy"]]}


def diagnose(state: RetrievalState) -> dict:
    """One decision-model call. Enough, or why not.

    TODO 3.3 (2 pts), with decide.

    decide.diagnose gives you the verdict and its probabilities. One thing to
    handle: absent is a judgment, and the model can be unsure of it. If it
    says absent with a probability under ABSENT_SURE and there are attempts
    left, call it wrong_words instead and let the graph search once more.
    Count the call.
    """
    # TODO 3.3
    # your code here
    raise NotImplementedError

def decide(state: RetrievalState) -> Literal["answer", "stronger", "plan"]:
    """Every verdict has one place to go. sufficient and absent both stop.
    incomplete needs a plan. wrong_words needs a stronger search, unless there
    is none left. And the attempt cap stops everything."""
    # TODO 3.3
    # your code here
    raise NotImplementedError

def stronger(state: RetrievalState) -> dict:
    """Same question, the next search up. STRONGER says which.

    TODO 3.4 (2 pts), with plan, execute and build_graph.
    """
    # TODO 3.4
    # your code here
    raise NotImplementedError

class Plan(BaseModel):
    """The separate questions a comparative question breaks into."""
    steps: list[str] = Field(description="Each names one company, one year if "
                                         "relevant, and one thing to find")


PLAN_PROMPT = """A question about SEC 10-K filings needs more than one search:

{question}

Passages found so far cover: {covered}

Write the separate questions still needed. Each must name exactly one company
and ask for one thing, so that a filtered search can find it. Fewest possible."""


def plan(state: RetrievalState) -> dict:
    """One chat-model call. Break the question into per-company searches.

    PLAN_PROMPT wants to know what the passages so far already cover, so the
    planner does not ask for it again. The sources of the documents in state
    are enough for that.
    """
    # TODO 3.4
    # your code here
    raise NotImplementedError

def execute(state: RetrievalState) -> dict:
    """One filtered search per step. The filter extractor is a chat call each.

    Append only passages you do not already have. documents has an add
    reducer, so return the new ones and the graph does the appending.
    """
    # TODO 3.4
    # your code here
    raise NotImplementedError

ANSWER_PROMPT = """Answer the question using only these passages from SEC
filings. Cite the filing each fact comes from, by its filename in brackets.
If the passages do not cover the question, say so in one sentence.

Question: {question}

Passages:
{passages}"""


def answer(state: RetrievalState) -> dict:
    """One chat-model call. The only place prose gets written."""
    if state.get("verdict") == "absent":
        return {"answer": "The filings in this corpus do not cover that.", "chat_calls": 0}
    out = retry(config.chat().invoke, ANSWER_PROMPT.format(
        question=state["question"], passages=format_passages(state["documents"])))
    return {"answer": text_of(out), "chat_calls": 1}


def build_graph():
    """Wire it as the diagram at the top of notebook 03 shows. decide and
    after_route return Literals, which declare their edges."""
    from langgraph.graph import StateGraph, START, END

    # TODO 3.4
    # your code here
    raise NotImplementedError

def run(question):
    """The whole final state, for tracing and for notebook 04's accounting."""
    return build_graph().invoke({"question": question, "attempts": 0,
                                 "chat_calls": 0, "decision_calls": 0})


def ask(question, verbose=False):
    state = run(question)
    if verbose:
        print(f"  {state['scope']} -> {state['strategy']}, verdict {state['verdict']}, "
              f"{state['attempts']} attempt(s), {state['chat_calls']} chat + "
              f"{state['decision_calls']} decision calls")
    return state["answer"]


# ---------------------------------------------------------------- the agent
#
# The graph above is the retrieval. The agent is what app.py serves: the same
# create_agent from W03b with two tools, the graph behind search_filings and
# the financials file behind financial_fact, and a checkpointer so the chat
# remembers the conversation. agentui.py streams it, tool calls and all.

def search_filings(question: str) -> str:
    """Answer a question from the text of the 10-K filings of NVIDIA, AMD and
    Micron: business, risk factors, management's discussion. Returns an answer
    with the filing each fact came from in brackets. Use financial_fact instead
    for a reported number such as revenue or R&D spend."""
    return run(question)["answer"]


SYSTEM_PROMPT = """You answer questions about NVIDIA, AMD and Micron from their
10-K filings. Use search_filings for anything the filings say in prose, and
financial_fact for a reported number. Relay the tool's answer, with its
citations, and do not add facts of your own. If the tools find nothing, say so."""


def build_agent():
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import MemorySaver

    return create_agent(config.chat(), tools=[search_filings, financial_fact],
                        system_prompt=SYSTEM_PROMPT, checkpointer=MemorySaver())
