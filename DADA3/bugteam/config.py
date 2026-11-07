"""Settings every other module reads.

Nothing here is a TODO. If you change a value, write down why in notebook 03: the team and the
baseline are only comparable when they ran under the same settings.
"""
import os

from dotenv import load_dotenv

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
REPO_DIR = os.path.join(BUNDLE, "repo")
ISSUES_FILE = os.path.join(BUNDLE, "issues.json")
RESULTS = os.path.join(BUNDLE, "results")
EVAL_DIR = os.path.join(BUNDLE, "eval")

# How many times the verifier may send one fix back to the fixer before the team gives up on it.
MAX_ROUNDS = 3

# How many issues the team works on at once. Each one has its own sandbox while it is verified.
MAX_PARALLEL = 2

# Where the verifier runs code: "daytona" (needs DAYTONA_API_KEY) or "docker" (needs Docker
# running, and the python:3.12-slim image pulled). Both are the sandboxes from W09b.2.
SANDBOX = os.getenv("SANDBOX", "daytona")

# The chat model plays every part. Mind the free-tier limits: 15 requests a minute and 500 a day.
# A team run on all ten issues is about 50 to 120 calls, and a baseline run about 10 to 20.
CHAT_MODEL = "gemini-3.5-flash-lite"

# For development without spending the Gemini quota: CHAT_BACKEND='ollama' in .env runs every chat
# call through Ollama instead. CHAT_BACKEND='openai' uses OPENAI_MODEL with your OPENAI_API_KEY, and
# CHAT_BACKEND='anthropic' uses ANTHROPIC_MODEL with your ANTHROPIC_API_KEY, if you have one.
CHAT_BACKEND = os.getenv("CHAT_BACKEND", "gemini")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3.5:9b")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")


def chat():
    """The chat model. No temperature: the flash-lite models use fixed sampling defaults and warn
    on every call if you pass one."""
    if CHAT_BACKEND == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=OLLAMA_CHAT_MODEL, reasoning=False)
    if CHAT_BACKEND == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=OPENAI_MODEL)
    if CHAT_BACKEND == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=ANTHROPIC_MODEL)
    if CHAT_BACKEND != "gemini":
        raise ValueError(f"CHAT_BACKEND is {CHAT_BACKEND!r}. Use gemini, ollama, openai, or anthropic.")
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=CHAT_MODEL, max_retries=8)


def model_name():
    """The model the current settings use, for the results files."""
    return {"ollama": OLLAMA_CHAT_MODEL, "openai": OPENAI_MODEL,
            "anthropic": ANTHROPIC_MODEL}.get(CHAT_BACKEND, CHAT_MODEL)
