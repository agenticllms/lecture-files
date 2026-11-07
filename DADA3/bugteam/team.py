"""Notebook 02: the whole team.

    START -> triage --one Send per bug--> fix   fix   fix ...   (a fixer-verifier pair each, in parallel)
               |                            |
               +--no bugs-------------------+--> report -> END

Triage makes one structured-output call per issue, as the reviewer did in W07b. The fan-out is the
one from W07a.2. Each fix is the pair from notebook 01.
"""
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field

from . import config
from .pair import fix_issue
from .repo import diff, issue_text, repo_files
from .util import retry, text_of


class Label(BaseModel):
    """The triage decision for one issue."""
    reasoning: str = Field(description="what the code does and what its docstring says, in at most 40 words")
    label: Literal["bug", "not_a_bug", "enhancement"] = Field(
        description="bug: the code does not do what its docstring says. "
                    "not_a_bug: it does, and the reporter expected something else. "
                    "enhancement: a request for something the docstring does not promise.")


TRIAGE_PROMPT = """You triage an open issue of huskyutils, a small Python library. Each function's
docstring is its specification. Read the code and the docstring of the function the issue is about,
decide whether the code does what the docstring says, and label the issue. Judge the behavior the
issue reports, not the fix it suggests.

The code:

{code}

The issue:

{issue}"""


REPORT_PROMPT = """You write the summary at the top of a maintainer's report on the open issues of
huskyutils. Below is what the team did on each issue. In one short paragraph, say which fixes were
verified and are ready to review, which issues still need a person, and which issues were closed
without a code change. Use only what is below. Do not add details.

{facts}"""


class TeamState(TypedDict):
    issues: list
    labels: dict                               # issue number -> bug, not_a_bug, or enhancement
    reasons: dict                              # issue number -> triage's reasoning
    results: Annotated[list, operator.add]     # one record per bug, from fix_issue
    report: str


def triage(state: TeamState) -> dict:
    """Label every issue, one structured-output call per issue."""
    # TODO 2.1
    # your code here
    raise NotImplementedError


def fan_out(state: TeamState):
    """One Send per issue triage labeled a bug, or straight to the report if there are none."""
    # TODO 2.2
    # your code here
    raise NotImplementedError


def fix(job: dict) -> dict:
    """One fixer-verifier pair. Its input is the Send's payload, not the team's state."""
    try:
        return {"results": [fix_issue(job["issue"], job["note"])]}
    except Exception as e:      # one failed issue should not lose the others
        issue = job["issue"]
        return {"results": [{"number": issue["number"], "title": issue["title"], "status": "error",
                             "rounds": 0, "fix": {}, "evidence": f"{type(e).__name__}: {e}"[:500],
                             "test": "", "log": []}]}


STATUS = {"verified": "fix verified", "rejected": "fix not verified", "no_fix": "no fix",
          "error": "stopped by an error"}


def outcome(state: TeamState, number: int) -> str:
    """What happened to one issue, in a few words."""
    for r in state["results"]:
        if r["number"] == number:
            return f"{STATUS[r['status']]}, {r['rounds']} verifier round(s)"
    return "not run" if state["labels"].get(number) == "bug" else "closed, no code change"


def facts(state: TeamState) -> list[str]:
    """One line per issue: its triage label and what happened to it."""
    return [f"#{i['number']} {i['title']}: {state['labels'].get(i['number'], 'not triaged')}; "
            f"{outcome(state, i['number'])}" for i in state["issues"]]


def summary(state: TeamState) -> str:
    """The paragraph at the top of the report, written by the model from the facts only."""
    # TODO 2.3
    # your code here
    raise NotImplementedError


def report(state: TeamState) -> dict:
    """The maintainer's report: the model's summary, then a table and one section per issue, filled in
    by code from what the agents recorded, so that no detail in them is made up."""
    files = repo_files()
    results = {r["number"]: r for r in state["results"]}
    table = ["| Issue | Triage | What happened |", "|---|---|---|"]
    sections = []
    for issue in state["issues"]:
        n = issue["number"]
        label = state["labels"].get(n, "not triaged")
        table.append(f"| #{n} {issue['title']} | {label} | {outcome(state, n)} |")
        part = [f"## #{n}: {issue['title']}", f"**Triage:** {label}. {state['reasons'].get(n, '')}"]
        r = results.get(n)
        if r and r["fix"]:
            fix = r["fix"]
            part += [f"**Fix** ({STATUS[r['status']]}): {fix['note']}",
                     "```diff\n" + diff(fix["path"], files[fix["path"]], fix["new_code"]).strip() + "\n```",
                     f"**Verifier:** {r['evidence'].strip()}"]
            if r["test"]:
                part.append(f"<details><summary>The verifier's test</summary>\n\n```python\n{r['test'].strip()}\n```\n\n</details>")
        elif r:
            part.append(f"**Fix:** none. {r['evidence'].strip()}")
        sections.append("\n\n".join(part))
    text = "\n\n".join(["# huskyutils: the open issues", summary(state), "\n".join(table)] + sections)
    return {"report": text}


def build_graph():
    # TODO 2.4
    # your code here
    raise NotImplementedError


def run(issues, callbacks=None):
    """One team run. MAX_PARALLEL issues are worked on at a time."""
    return build_graph().invoke({"issues": issues},
                                {"max_concurrency": config.MAX_PARALLEL, "recursion_limit": 60,
                                 **({"callbacks": callbacks} if callbacks else {})})
