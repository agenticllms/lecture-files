"""Notebook 01: the verifier, a deep agent that runs the fix in a sandbox.

It gets the issue and the name of the changed file, but not the change itself, so that its test
comes from the issue and the docstring. It ends its run by calling one of two handoff tools.
"""
from deepagents import create_deep_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from langgraph.errors import GraphRecursionError

from . import config
from .repo import issue_text, repo_files
from .sandbox import open_sandbox, read_sandbox_file, upload_files

VERIFIER_PROMPT = """You check a proposed fix for one issue in huskyutils, a small Python library.
Another agent wrote the fix. You are not shown the change, so that your tests come from the issue
and the docstring and not from the fix. Your files are under {workdir}:

- {workdir}/original/ is the repository before the fix
- {workdir}/fixed/ is the repository with the fix

Run Python with execute. The tests use unittest. To run them, cd into one of the two folders and run
`python -m unittest discover -s tests -v`.

1. Read the issue, and the docstring of the function it is about. The docstring is the specification.
2. Write tests/test_issue.py in both folders. It checks what the issue and the docstring say the
   function should do, including every example in the docstring. Write it from the issue and the
   docstring, not from the fix. Test only inputs the docstring allows: if it says a value is at
   least 1, do not test 0.
3. Run all the tests in both folders. Your test should fail in original/, which shows it reproduces
   the issue; that failure is what you want, not a reason to reject the fix. In fixed/, every test
   should pass, yours and the ones that were already there.

Then call exactly one of these tools, and stop:
- accept_fix, if your test fails in original/ and every test passes in fixed/. Give the commands you
  ran and the result.
- transfer_to_fixer, otherwise. Give the failing test and its output, so that the fixer can see
  what is wrong. If your test passes in original/, it does not reproduce the issue: correct your
  test before you decide."""


# TODO 1.3: both tools must end the verifier's run when they are called.
def accept_fix(evidence: str) -> str:
    """Accept the fix. evidence: the commands you ran and what they showed, briefly."""
    # your code here
    raise NotImplementedError


def transfer_to_fixer(reason: str) -> str:
    """Send the fix back to the fixer. reason: what is wrong, with the failing test and its output."""
    # your code here
    raise NotImplementedError


def decision(messages):
    """('accept', evidence) or ('reject', reason) from the verifier's last handoff call, or
    ('none', '') if it stopped without calling either."""
    # TODO 1.3
    # your code here
    raise NotImplementedError


def verify(issue, fix):
    """Run the verifier on one fix, in a new sandbox. fix is the fixer's transfer_to_verifier arguments.

    Returns {"decision": "accept" | "reject" | "none", "message": ..., "test": the test it wrote}."""
    # TODO 1.4
    # your code here
    raise NotImplementedError
