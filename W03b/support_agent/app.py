"""Deployment entry point: the support agent behind a chat UI.

    python app.py

Opens the same Gradio interface as the end of W03b.1. This file is what a
hosting platform would run; the notebook was where we figured out what to run.
Nothing to transfer here — once agent/ is complete, this just works.
"""

from agentui import GradioUI

from agent.agent import support_agent

ui = GradioUI(support_agent,
              {"configurable": {"thread_id": "web-demo"}},
              title="Husky Tech Support")

# Spaces imports this file and serves the module-level `demo` object itself;
# the launch() below only runs when you start the app locally.
demo = ui.interface()

if __name__ == "__main__":
    demo.launch()
