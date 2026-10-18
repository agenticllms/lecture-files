"""Settings every other module reads.

Nothing here is a TODO. Change a value if you have a reason to, but write the
reason down in notebook 04, because changing two things at once is how an
ablation study stops meaning anything.
"""
import os
from dotenv import load_dotenv

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_bundle(start):
    """Walk up until we find the folder holding corpus/manifest.csv, so these
    modules keep working if you move them or run them from somewhere else."""
    here = start
    for _ in range(5):
        for candidate in (here, os.path.join(here, "student_bundle")):
            has_corpus = os.path.exists(os.path.join(candidate, "corpus", "manifest.csv"))
            has_eval = os.path.isdir(os.path.join(candidate, "eval"))
            if has_corpus and has_eval:     # a corpus copy alone is not the bundle
                return candidate
        here = os.path.dirname(here)
    return os.path.dirname(start)


BUNDLE = _find_bundle(os.path.dirname(HERE))
CORPUS = os.path.join(BUNDLE, "corpus")
SECTIONS = os.path.join(CORPUS, "sections")
FINANCIALS = os.path.join(CORPUS, "financials")
MANIFEST = os.path.join(CORPUS, "manifest.csv")
EVAL_DIR = os.path.join(BUNDLE, "eval")

# Chunking. These are the values the reference solution used.
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150

# Embeddings. Three backends, and the index is named after the vector size, so
# an index built with one backend is only ever searched with a backend that
# produces the same vectors.
#
#   cloudflare  qwen3-embedding-0.6b hosted on Workers AI. Default. Free, no
#               install, the whole corpus in about four minutes, and the
#               deployed app uses it too. 1024 dimensions.
#   ollama      the same model, local. The backup. Its vectors match
#               Cloudflare's, so it reads and writes the same index.
#   gemini      models/gemini-embedding-001, the lecture model. 3072
#               dimensions. The free tier allows 1,000 embeddings a day, and
#               this corpus is 2,124 chunks, so indexing with it needs the
#               paid tier. Fine for embedding questions.
EMBEDDINGS = os.getenv("EMBEDDINGS", "cloudflare")
EMBED_MODELS = {"gemini": "models/gemini-embedding-001",
                "ollama": "qwen3-embedding:0.6b",
                "cloudflare": "@cf/qwen/qwen3-embedding-0.6b"}
EMBED_MODEL = EMBED_MODELS[EMBEDDINGS]
EMBED_BATCH = 64          # larger batches make Ollama drop the connection

# The chat model is a paid-but-free-tier API. Mind the two limits: 15 requests
# a minute and 500 a day. An evaluation run over 14 questions times 5
# strategies is well over 100 calls, so pace it.
CHAT_MODEL = "gemini-3.5-flash-lite"

# Retrieval
K = 5                     # passages handed to the model
POOL = 10                 # candidates a reranker gets to reorder
RRF_K = 60                # the constant in reciprocal rank fusion

TICKERS = ("NVDA", "AMD", "MU")


def embeddings():
    if EMBEDDINGS == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    if EMBEDDINGS == "cloudflare":
        from .embed import CloudflareEmbeddings
        return CloudflareEmbeddings()
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(model=EMBED_MODEL)


def index_name(dim):
    """Vectors from two embedding models cannot share an index, so the
    dimension goes in the name and the mistake becomes impossible. If you
    named your index something else, put INDEX_NAME in .env and every
    notebook and the app will use that instead."""
    return os.getenv("INDEX_NAME") or f"dada2-{dim}"


# For local testing without spending the Gemini quota: CHAT_BACKEND=ollama in
# .env runs the chat model through Ollama instead. Not for students.
CHAT_BACKEND = os.getenv("CHAT_BACKEND", "gemini")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3.5:4b")


def chat():
    """The chat model. No temperature: the flash-lite models use fixed
    sampling defaults and warn on every call if you pass one."""
    if CHAT_BACKEND == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=OLLAMA_CHAT_MODEL, reasoning=False)
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=CHAT_MODEL)


# Cloudflare Workers AI, for the decision model in notebook 03. Both come from
# the Cloudflare dashboard. The token needs the Workers AI permission.
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CLOUDFLARE_API_KEY")
DECISION_MODEL = "clef-flash"       # or "clef", slower and a little more accurate
