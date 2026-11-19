"""The chat interface customers see. Each browser session is its own conversation."""
import os

import gradio as gr
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_agent, load_model

agent = build_agent(load_model(os.getenv("MODEL", "gpt-4.1-mini")), checkpointer=InMemorySaver())


def respond(message, history, request: gr.Request):
    config = {"configurable": {"thread_id": request.session_hash}}
    out = agent.invoke({"messages": [HumanMessage(content=message)]}, config)
    return out["messages"][-1].text


demo = gr.ChatInterface(respond, title="Husky Tech Support",
                        examples=["My headphones from order HT-2001 crackle. Can I get a refund?",
                                  "How long does shipping take?"])
