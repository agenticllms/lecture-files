"""The deployable app: the agent from rag/agent.py behind the course's Gradio UI.

    python app.py            # http://localhost:7860

agentui.py is the same file as W03b, W05b and DADA1. It streams the agent
node by node, so each tool call shows up in the chat as a collapsible entry
before the answer, and the checkpointer keeps the conversation. Nothing to
implement here; it works once notebooks 01 to 03 are done.
"""
import os

from agentui import GradioUI
from rag import agent, config

demo = GradioUI(
    agent.build_agent(),
    title="SEC filings agent",
    description=("Four fiscal years of 10-K filings from NVIDIA, AMD and Micron. "
                 "search_filings runs the diagnosing retrieval graph; financial_fact "
                 f"reads the XBRL figures. Chat model: {config.CHAT_MODEL}."),
).interface()

if __name__ == "__main__":
    # Render sets PORT and needs 0.0.0.0. Locally this is http://localhost:7860.
    # show_error puts the exception text in the chat, so a bad key or an exhausted
    # quota reads as what it is instead of a bare "Error".
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)),
                show_error=True)
