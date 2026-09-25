"""Deployment entry point: the support agent behind a chat UI.

    python app.py

Opens the same Gradio interface as the end of W03b.1. This file is what a
hosting platform would run; the notebook was where we figured out what to run.
Nothing to transfer here — once agent/ is complete, this just works.
"""

# This try/except block is only needed to deploy on HuggingFace Spaces
# ZeroGPU hardware refuses to start unless it detects one @spaces.GPU function.
# This app never needs a GPU (the model is an API call), so we register a decoy.
# Locally the `spaces` package does not exist and this block is skipped.
try:
    import spaces

    @spaces.GPU
    def _zero_gpu_probe():
        """Never called. Exists only so ZeroGPU hardware lets the app start."""
        return "unused"
except ImportError:
    pass

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
