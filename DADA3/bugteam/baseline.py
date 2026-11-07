"""The baseline: one deep agent does the whole job in one sandbox. Given.

It has the same model, the same sandbox, and the same issues as the team. The difference is that
nobody but the agent itself checks its fixes.
"""
import os
from typing import Literal

from deepagents import create_deep_agent
from langchain.messages import HumanMessage
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel, Field

from . import config
from .repo import issue_text, repo_files
from .sandbox import open_sandbox, read_sandbox_file, save_files, upload_files
from .util import retry, text_of

BASELINE_PROMPT = """You maintain huskyutils, a small Python library. Its files are in {workdir}/repo.
Each function's docstring is its specification. Run Python with execute; the tests use unittest
(cd {workdir}/repo && python -m unittest discover -s tests -v).

For every open issue:
1. Decide whether it is a bug (the code does not do what its docstring says), not_a_bug (the code
   does what its docstring says), or an enhancement (a request for new behavior).
2. For a bug, fix the code in {workdir}/repo/huskyutils/. Do not change the tests or the docstrings.
   Check your fix by running code.

When you are done, write {workdir}/REPORT.md, a short report for the maintainer with one section per
issue: your decision, what you changed, and how you checked it."""

READ_PROMPT = """Below is a maintainer's report on the open issues of a Python library. For every issue
it covers, give its number, the label the report gives it, and whether the report says the bug was
fixed and the fix was checked by running code. Use only what the report says.

{report}"""


class Decision(BaseModel):
    """The baseline's decision on one issue."""
    number: int
    label: Literal["bug", "not_a_bug", "enhancement"]
    fixed: bool = Field(description="true if this is a bug and you fixed it and checked the fix by running code")


class Decisions(BaseModel):
    """The decisions, one per issue."""
    items: list[Decision]


def run(issues, callbacks=None, out_dir=None):
    """Run the baseline once. Returns its triage, its claims, its changed files, and its report."""
    files = repo_files()
    model = config.chat()
    with open_sandbox() as (sandbox, workdir):
        upload_files(sandbox, files, f"{workdir}/repo")
        agent = create_deep_agent(model=model, system_prompt=BASELINE_PROMPT.format(workdir=workdir),
                                  backend=sandbox)
        request = "The open issues:\n\n" + "\n\n---\n\n".join(issue_text(i) for i in issues)
        run_config = {"recursion_limit": 250, **({"callbacks": callbacks} if callbacks else {})}
        try:
            out = agent.invoke({"messages": [HumanMessage(content=request)]}, run_config)
            final, finished = text_of(out["messages"][-1]), True
        except GraphRecursionError:
            final, finished = "", False
        report = read_sandbox_file(sandbox, f"{workdir}/REPORT.md")
        changed = {}
        for path in files:
            if path.startswith("huskyutils/"):
                now = read_sandbox_file(sandbox, f"{workdir}/repo/{path}")
                if now and now != files[path]:
                    changed[path] = now
        if out_dir:
            save_files(sandbox, f"{workdir}/repo", os.path.join(out_dir, "repo"))
    # The labels and claims come from the report, read by one structured-output call, the way
    # file_ticket read the conversation in W03b. The team's triage is structured output too.
    written = report or final
    decided = retry(model.with_structured_output(Decisions).invoke, READ_PROMPT.format(report=written),
                    **({"config": {"callbacks": callbacks}} if callbacks else {})) if written else None
    items = decided.items if decided else []
    triage = {d.number: d.label for d in items}
    claims = {d.number: d.fixed and d.label == "bug" for d in items}
    return {"finished": finished, "triage": triage, "claims": claims, "report": written,
            "patches": [{"path": p, "code": c} for p, c in changed.items()]}
