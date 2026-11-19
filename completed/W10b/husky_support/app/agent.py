"""The support agent: the Week 4 loop of an assistant node and a tool node.

The deployed app and the evaluation suite both build the agent with build_agent, so the evaluation
tests the same code that customers use.
"""
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from app import store


def load_model(name):
    """A chat model by name, such as "gpt-4.1-mini", "claude-haiku-5-5",
    "google_genai:gemini-3.5-flash-lite", or "ollama:qwen3.5:9b"."""
    return init_chat_model(name)


def build_agent(model, prompt=store.POLICY_PROMPT, checkpointer=None):
    model_with_tools = model.bind_tools(store.TOOLS)
    sys_msg = SystemMessage(content=prompt)

    def assistant(state: MessagesState) -> dict:
        return {"messages": [model_with_tools.invoke([sys_msg] + state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(store.TOOLS))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    return builder.compile(checkpointer=checkpointer)
