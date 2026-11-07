"""Notebook 01: the fixer. It reads the code and writes a fix, but it cannot run anything.

    START -> assistant -> tools -> assistant -> ... -> transfer_to_verifier -> END

The W04b loop, with the rule from W08a: once the handoff tool has run, the agent stops, and the graph
around it decides who works next.
"""
from langchain.messages import SystemMessage
from langchain.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from . import config
from .repo import repo_files
from .util import retry

FIXER_PROMPT = """You fix one bug in huskyutils, a small Python library. You can read the repository's
files, but you cannot run code. Another agent, the verifier, runs your fix in a sandbox.

- Read the files the issue is about with read_file. The function's docstring is its specification:
  when the code and the docstring disagree, change the code to match the docstring.
- Change as little as you can, and only one file. Do not change the tests or the docstring.
- When the fix is ready, call transfer_to_verifier with the path of the file, its complete new
  content, and a note that says what was wrong and what you changed.
- If the verifier sends the fix back, read its reason and the failing output, correct the fix,
  and call transfer_to_verifier again."""

@tool
def list_files() -> str:
    """List the files in the repository."""
    return "\n".join(repo_files())


@tool
def read_file(path: str) -> str:
    """Read one file of the repository, for example huskyutils/text.py."""
    # TODO 1.1
    # your code here
    raise NotImplementedError


@tool
def transfer_to_verifier(path: str, new_code: str, note: str) -> str:
    """Hand your fix to the verifier. path: the file you changed. new_code: the complete new content of
    that file. note: what was wrong and what you changed, in one or two sentences."""
    # TODO 1.1
    # your code here
    raise NotImplementedError


TOOLS = [list_files, read_file, transfer_to_verifier]


def after_tools(state: MessagesState) -> str:
    """After the tools run: stop if the fix was handed over, otherwise back to the model."""
    # TODO 1.2
    # your code here
    raise NotImplementedError


def build_fixer():
    model_with_tools = config.chat().bind_tools(TOOLS)
    sys_msg = SystemMessage(content=FIXER_PROMPT)

    def assistant(state: MessagesState) -> dict:
        return {"messages": [retry(model_with_tools.invoke, [sys_msg] + state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_conditional_edges("tools", after_tools, ["assistant", END])
    return builder.compile()


def find_fix(messages):
    """The arguments of the last transfer_to_verifier call in messages, or None if there is none."""
    for m in reversed(messages):
        for call in getattr(m, "tool_calls", None) or []:
            if call["name"] == "transfer_to_verifier":
                return call["args"]
    return None
