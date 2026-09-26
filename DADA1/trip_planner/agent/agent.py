"""Trip planner agent

    python -m agent.agent
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

# silence a noisy advisory warning from the Google SDK
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

# Fail fast and legibly: a placeholder left over from example.env otherwise
# surfaces as a 400 INVALID_ARGUMENT deep inside the first model call.
for _name in ("GOOGLE_API_KEY", "TAVILY_API_KEY"):
    if os.getenv(_name, "").startswith("your_"):
        raise SystemExit(
            f"{_name} in your .env is still the placeholder from example.env. "
            "Replace it with your real key, in .env at your project root."
        )

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

# TODO: Import your tools and system prompt

# You must use an API model for online deployment. Otherwise, we cannot test it properly.
# Options: Gemini, OpenRouter, NVIDIA as posted on Piazza
model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# Local alternative for testing during development
# from langchain_ollama import ChatOllama
# model = ChatOllama(model="qwen3.5:4b", reasoning=False)

# TODO: create the trip_agent instance


def ask(text: str, thread: str) -> dict:
    """One turn of the conversation. The same thread keeps the memory."""
    # TODO: implement the ask function to interact with the trip_agent

if __name__ == "__main__":
    from .itinerary import build_itinerary

    print("Trip planner. Describe your trip, refine it, then type 'quit'.")
    result = None
    while True:
        user = input("You: ")
        if user.lower() in {"quit", "exit"}:
            break
        result = ask(user, "cli-demo")
        print("Agent:", result["messages"][-1].text)

    if result is not None:
        print("\n--- itinerary ---")
        print(build_itinerary(model, result).model_dump_json(indent=2))
