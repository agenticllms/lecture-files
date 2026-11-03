"""Tools for the deep research agent. Week 7.

Two sources behind the same two tools:

    cache   papers.json, shipped with this folder. The default in lecture,
            so a demo never waits on an API or trips a rate limit.
    live    arXiv through the arxiv client (one request every three seconds,
            which is arXiv's rule), or Semantic Scholar if S2_API_KEY is set.

Set PAPER_SOURCE=live in .env to search for real. Both tools return plain
strings with the paper id in front, so the agent can cite a paper and ask
for it again.
"""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(HERE, "papers.json")


def source():
    return os.getenv("PAPER_SOURCE", "cache")


# ------------------------------------------------------------------ the cache

_cache = None


def cache():
    global _cache
    if _cache is None:
        with open(CACHE_PATH) as f:
            _cache = json.load(f)
    return _cache


def _bm25():
    """Lexical search over the cache, so a cached search behaves like a
    search and not like a lookup: close wording finds a paper, vague
    wording finds the wrong ones."""
    from rank_bm25 import BM25Okapi
    papers = list(cache()["papers"].values())
    docs = [(p["title"] + " " + p["abstract"]).lower().split() for p in papers]
    return papers, BM25Okapi(docs)


def _cache_search(query, limit):
    papers, index = _bm25()
    scores = index.get_scores(query.lower().split())
    best = sorted(range(len(papers)), key=lambda i: -scores[i])[:limit]
    return [papers[i] for i in best if scores[i] > 0]


# ------------------------------------------------------------------ live: arXiv

def _arxiv_search(query, limit):
    import arxiv
    client = arxiv.Client(page_size=limit, delay_seconds=3.0, num_retries=4)
    results = client.results(arxiv.Search(query=query, max_results=limit))
    return [_from_arxiv(r) for r in results]


def _arxiv_get(paper_id):
    import arxiv
    client = arxiv.Client(delay_seconds=3.0, num_retries=4)
    results = list(client.results(arxiv.Search(id_list=[paper_id])))
    return _from_arxiv(results[0]) if results else None


def _from_arxiv(r):
    return {
        "id": r.get_short_id().split("v")[0],
        "title": " ".join(r.title.split()),
        "abstract": " ".join(r.summary.split()),
        "authors": [a.name for a in r.authors],
        "year": r.published.year,
        "published": r.published.date().isoformat(),
        "categories": list(r.categories),
        "url": r.entry_id,
        "citation_count": None,
        "source": "arxiv",
    }


# ------------------------------------------------- live: Semantic Scholar

S2 = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,year,venue,citationCount,abstract,authors,externalIds,url"


def _s2(path, params):
    """One Semantic Scholar call, retrying on 429. Without a key you share a
    pool with everyone else on the internet, and 429 is common; with a key
    you get one request a second of your own."""
    import requests
    headers = {"x-api-key": os.environ["S2_API_KEY"]} if os.getenv("S2_API_KEY") else {}
    for attempt in range(6):
        r = requests.get(S2 + path, params=params, headers=headers, timeout=30)
        if r.status_code != 429:
            r.raise_for_status()
            return r.json()
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("Semantic Scholar kept answering 429. Get a key, or wait.")


def _s2_search(query, limit):
    data = _s2("/paper/search", {"query": query, "limit": limit, "fields": S2_FIELDS})
    return [_from_s2(p) for p in data.get("data", [])]


def _from_s2(p):
    ids = p.get("externalIds") or {}
    return {
        "id": ids.get("ArXiv") or p["paperId"],
        "title": p.get("title") or "",
        "abstract": p.get("abstract") or "",
        "authors": [a["name"] for a in p.get("authors") or []],
        "year": p.get("year"),
        "published": None,
        "categories": [],
        "url": p.get("url"),
        "citation_count": p.get("citationCount"),
        "venue": p.get("venue"),
        "source": "semanticscholar",
    }


# ----------------------------------------------------------------- the tools

def _line(p, chars=220):
    who = ", ".join(p["authors"][:3]) + (" et al." if len(p["authors"]) > 3 else "")
    cites = f", {p['citation_count']} citations" if p.get("citation_count") is not None else ""
    return f"[{p['id']}] {p['title']} ({p['year']}{cites}). {who}.\n    {p['abstract'][:chars]}..."


def search_papers(query: str, limit: int = 8) -> str:
    """Search the literature. Returns up to `limit` papers, each with its id in
    brackets, title, year, authors and the start of the abstract. Use
    get_paper with the id to read a full abstract."""
    src = source()
    if src == "cache":
        hits = _cache_search(query, limit)
    elif src == "live" and os.getenv("S2_API_KEY"):
        hits = _s2_search(query, limit)
    else:
        hits = _arxiv_search(query, limit)
    if not hits:
        return "No papers found. Try different words."
    return "\n".join(_line(p) for p in hits)


def get_paper(paper_id: str) -> str:
    """The full record for one paper id from a search: title, authors, year,
    and the whole abstract."""
    paper_id = paper_id.strip("[] ").replace("arxiv:", "")
    p = cache()["papers"].get(paper_id)
    if p is None and source() != "cache":
        p = _arxiv_get(paper_id)
    if p is None:
        return f"No paper with id {paper_id}. Ids come from search_papers."
    who = ", ".join(p["authors"])
    return f"[{p['id']}] {p['title']} ({p['year']})\n{who}\n{p.get('url') or ''}\n\n{p['abstract']}"


# ------------------------------------------------------------------ scoring

def questions():
    """The example questions, each with the papers it should find."""
    return cache()["questions"]


def found_ids(text):
    """Every paper id cited in a piece of text. Accepts [2503.13657],
    [2503.13657, 2308.08155], [arXiv:2503.13657], 2503.13657v2, and a bare
    id in prose; the model is asked for brackets and does not always comply."""
    import re
    return sorted(set(re.findall(r"(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?![\d.])", text)))


def score_coverage(text, gold):
    """What fraction of the gold papers the text cites."""
    ids = set(found_ids(text))
    return len([g for g in gold if g in ids]) / len(gold)
