"""The W07a research team as a module, so later notebooks build on it the
way the support agent built on support_tools.py.

    import research_team as team
    single = team.build_single(model)
    crew = team.build_team(model)
    team.run_team(crew, question)   -> report, findings, tokens, seconds

Everything here is the code from W07a.2, unchanged except that the model is
passed in rather than assumed.
"""
import operator
import time
from typing import Annotated, TypedDict

from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Send
from pydantic import BaseModel, Field

import research_tools as rt

SINGLE_PROMPT = """You are a research assistant. Answer the question from the literature.
Search with search_papers, read the papers that matter with get_paper, and
write a short report: what is known, with every claim followed by the id of
the paper that supports it, in brackets like [2503.13657]. Cite only papers
you have read. Search more than once if the question has more than one part."""

WORKER_PROMPT = """You are a research assistant working on one sub-question of a
larger question. Start with a search that uses the sub-question's own words.
Read the two to four papers that matter with get_paper, preferring the papers
that introduced a system or method over papers that only apply or extend it.
Write a finding of at most 150 words: what those papers say about the
sub-question, with each claim followed by the paper id in brackets like
[2503.13657]. Cite only papers you have read."""

PLAN_PROMPT = """A research question: {question}

Split it into three sub-questions that together cover it and do not overlap.
Every sub-question must stay on the question's own subject and reuse its key
terms, so that a literature search for the sub-question finds papers about
this question and not about a neighboring topic. Cover: the main systems or
methods that have been proposed, the problems or failures that have been
reported, and what has been measured or compared."""

SYNTH_PROMPT = """Question: {question}

Findings from three researchers, each on one part of the question:

{findings}

Write the report: what is known, organized by the parts of the question, with
every claim followed by the paper id in brackets as the findings give it. Keep
every paper the findings cite; do not drop a citation when you condense, and
do not add papers the findings did not cite."""


# ----------------------------------------------------------------- helpers

def tokens_of(messages):
    """Total tokens the model reported across a run."""
    return sum((m.usage_metadata or {}).get("total_tokens", 0)
               for m in messages if getattr(m, "usage_metadata", None))


def tool_calls_of(messages):
    """The tool calls in a run, in order, as (tool, first argument)."""
    calls = []
    for m in messages:
        for call in getattr(m, "tool_calls", None) or []:
            first = next(iter(call["args"].values()), "")
            calls.append((call["name"], str(first)[:60]))
    return calls


def format_findings(findings):
    return "\n\n".join(f"Sub-question: {q}\n{f}" for q, f in findings)


# ------------------------------------------------------------- one agent

def build_agent(model, system_prompt, tools=None):
    """The tool loop from W04b: assistant -> tools -> assistant, until the
    model stops calling tools. Compiled, so it can be a node in a larger graph."""
    tools = tools or [rt.search_papers, rt.get_paper]
    model_with_tools = model.bind_tools(tools)
    sys_msg = SystemMessage(content=system_prompt)

    def assistant(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke([sys_msg] + state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("assistant", assistant)
    g.add_node("tools", ToolNode(tools))
    g.add_edge(START, "assistant")
    g.add_conditional_edges("assistant", tools_condition)
    g.add_edge("tools", "assistant")
    return g.compile()


def build_single(model):
    return build_agent(model, SINGLE_PROMPT)


def run_single(agent, question):
    start = time.time()
    messages = agent.invoke({"messages": [HumanMessage(content=question)]})["messages"]
    return {"report": messages[-1].text, "messages": messages,
            "tokens": tokens_of(messages), "seconds": time.time() - start,
            "calls": tool_calls_of(messages)}


# ------------------------------------------------------- orchestrator, workers

class ResearchState(TypedDict):
    question: str
    sub_questions: list
    findings: Annotated[list, operator.add]
    tokens: Annotated[int, operator.add]
    report: str


class WorkerState(TypedDict):
    sub_question: str


class Plan(BaseModel):
    """The parts of a research question that need their own search."""
    sub_questions: list[str] = Field(
        description="Three sub-questions. Each covers a different part of the "
                    "question and is specific enough to search for on its own.")


def build_team(model, with_report=True, tools=None):
    """plan -> research (one worker per sub-question, in parallel) -> synthesize.
    with_report=False stops after research: findings only, for a team where
    someone else writes. tools= replaces the workers' tools, which are
    search_papers and get_paper unless you say otherwise."""
    planner = model.with_structured_output(Plan)
    worker = build_agent(model, WORKER_PROMPT, tools)      # the same loop, one per sub-question

    def plan(state: ResearchState) -> dict:
        out = planner.invoke(PLAN_PROMPT.format(question=state["question"]))
        return {"sub_questions": out.sub_questions}

    def research(state: WorkerState) -> dict:
        messages = worker.invoke({"messages": [HumanMessage(content=state["sub_question"])]})["messages"]
        return {"findings": [(state["sub_question"], messages[-1].text)],
                "tokens": tokens_of(messages)}

    def fan_out(state: ResearchState):
        return [Send("research", {"sub_question": q}) for q in state["sub_questions"]]

    def synthesize(state: ResearchState) -> dict:
        out = model.invoke(SYNTH_PROMPT.format(question=state["question"],
                                               findings=format_findings(state["findings"])))
        return {"report": out.text, "tokens": tokens_of([out])}

    g = StateGraph(ResearchState)
    g.add_node("plan", plan)
    g.add_node("research", research)
    g.add_edge(START, "plan")
    g.add_conditional_edges("plan", fan_out, ["research"])
    if with_report:
        g.add_node("synthesize", synthesize)
        g.add_edge("research", "synthesize")
        g.add_edge("synthesize", END)
    else:
        g.add_edge("research", END)
    return g.compile()


def run_team(crew, question):
    start = time.time()
    result = crew.invoke({"question": question, "findings": [], "tokens": 0})
    return {"report": result.get("report", ""), "sub_questions": result["sub_questions"],
            "findings": result["findings"], "tokens": result["tokens"],
            "seconds": time.time() - start}
