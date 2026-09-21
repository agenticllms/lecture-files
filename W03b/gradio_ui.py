"""A minimal Gradio chat UI for LangGraph / LangChain agents.

Usage (mirrors the in-class demo):

    from gradio_ui import GradioUI

    app = GradioUI(agent, config)
    app.launch()

What it does:
- Streams the agent's execution node by node, so tool calls appear in the chat
  as they happen, before the final answer.
- Renders each tool call as a collapsible entry (Gradio does this automatically
  for any ChatMessage whose metadata has a "title").
- Leaves conversation memory to the agent's checkpointer: because the same
  thread_id is sent on every turn, the graph itself remembers the conversation.
  Gradio's visible history is display-only.

Requires: gradio >= 5 (`uv pip install gradio`), a compiled LangGraph agent
(e.g. from `create_agent(..., checkpointer=MemorySaver())`).
"""

from __future__ import annotations

import json
import uuid

import gradio as gr
from langchain.messages import HumanMessage


def _text_of(message) -> str:
    """Message content can be a plain string or a list of content blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


class GradioUI:
    def __init__(self, agent, config=None, title="LangGraph Agent", description=None):
        self.agent = agent
        # If no config is given, make a fresh conversation thread for this session.
        self.config = config or {"configurable": {"thread_id": uuid.uuid4().hex}}
        self.title = title
        self.description = description

    # ------------------------------------------------------------------
    # The chat function Gradio calls on every user turn.
    # It is a *generator*: each `yield` updates the UI, which is how the
    # tool-call entries show up before the final answer is ready.
    # ------------------------------------------------------------------
    def _chat(self, user_message, history):
        shown = []

        stream = self.agent.stream(
            {"messages": [HumanMessage(content=user_message)]},
            self.config,
            stream_mode="updates",  # one update per graph node that ran
        )

        for update in stream:
            for _node, payload in update.items():
                for message in (payload or {}).get("messages", []):
                    shown.extend(self._render(message))
                    yield shown

        if not shown:
            yield [gr.ChatMessage(role="assistant",
                                  content="(the agent produced no output)")]

    # ------------------------------------------------------------------
    # Turn one LangChain message into zero or more Gradio ChatMessages.
    # ------------------------------------------------------------------
    def _render(self, message):
        rendered = []
        kind = getattr(message, "type", None)

        if kind == "ai":
            # 1) Any tool calls the model decided to make -> collapsible entries
            for call in getattr(message, "tool_calls", None) or []:
                args = json.dumps(call.get("args", {}), indent=2, ensure_ascii=False)
                rendered.append(gr.ChatMessage(
                    role="assistant",
                    content=f"```json\n{args}\n```",
                    metadata={"title": f"🛠️ Used tool {call['name']}"},
                ))
            # 2) Any plain text (usually the final answer)
            text = _text_of(message)
            if text.strip():
                rendered.append(gr.ChatMessage(role="assistant", content=text))

        elif kind == "tool":
            # The tool's return value -> its own collapsible entry
            rendered.append(gr.ChatMessage(
                role="assistant",
                content=f"```\n{_text_of(message)}\n```",
                metadata={"title": f"📄 Result from {getattr(message, 'name', 'tool')}"},
            ))

        return rendered

    # ------------------------------------------------------------------
    def launch(self, **kwargs):
        interface_kwargs = dict(
            fn=self._chat,
            title=self.title,
            description=self.description,
        )
        # Gradio 5 needs type="messages" to accept ChatMessage objects;
        # Gradio 6 removed the parameter (messages is the only format).
        import inspect
        if "type" in inspect.signature(gr.ChatInterface.__init__).parameters:
            interface_kwargs["type"] = "messages"
        demo = gr.ChatInterface(**interface_kwargs)
        return demo.launch(**kwargs)
