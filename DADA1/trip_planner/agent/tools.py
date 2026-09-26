"""Trip planner: Tools

Two rules, the same ones from the Husky Tech agent:
  1. Return a readable string. Never raise, never return a bare dict.
  2. When you have nothing useful, SAY SO in the return value. "No results —
     try a nearby larger city" is a sentence the model can act on.
"""

import os
from datetime import datetime, timedelta

import requests
from langchain.tools import tool
from langchain_tavily import TavilySearch

# Use these URLs for their corresponding tools
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

FORECAST_DAYS = 16          # all Open-Meteo will forecast: today + 15
MAX_RESULTS = 3

# Open-Meteo returns a WMO code, not words. Only the common ones are listed;
# anything else falls through to "code N", which will keep the agent honest.
WEATHER_CODES = {
    0: "clear", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "freezing fog", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    66: "freezing rain", 67: "freezing rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 77: "snow grains", 80: "rain showers", 81: "rain showers",
    82: "violent rain showers", 85: "snow showers", 86: "snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


def _search(query: str) -> str:
    """Run one web search and format the hits. Shared by the four find_* tools."""
    try:
        results = TavilySearch(max_results=MAX_RESULTS).invoke({"query": query})
    except Exception as e:
        return f"The search failed ({e}). Tell the user you could not look this up."

    hits = results.get("results", []) if isinstance(results, dict) else []
    if not hits:
        return (f"No results for '{query}'. Try a nearby larger city, or tell the "
                f"user you could not find anything — do not fill the gap from memory.")

    lines = []
    for i, h in enumerate(hits, 1):
        snippet = " ".join((h.get("content") or "").split())[:300]
        lines.append(f"{i}. {h.get('title', 'untitled')}\n   {h.get('url', '')}\n   {snippet}")
    return "\n".join(lines) + (
        "\nThese snippets are the only evidence you have. They do not include "
        "opening hours, and a price counts only if it is written above.")


def _geocode(city: str) -> tuple[str, float, float, str]:
    """City name -> (label, latitude, longitude, ambiguity_note). Written for you.

    Raises ValueError if nothing matches. The ambiguity note is the interesting
    part: this API ranks by population, so "Cambridge" puts England ahead of
    Massachusetts and "Portland" puts Oregon ahead of Maine.
    """
    r = requests.get(GEOCODE_URL, params={"name": city.strip(), "count": 5,
                                          "language": "en", "format": "json"},
                     timeout=15)
    r.raise_for_status()
    results = (r.json() or {}).get("results") or []
    if not results:
        raise ValueError(f"No place matches '{city}'.")

    def describe(r):
        return ", ".join(x for x in (r["name"], r.get("admin1"), r.get("country")) if x)

    top = results[0]
    label = describe(top)

    # Every US city shares its name with a hamlet somewhere; "Boston, Georgia (pop. 1,400)"
    # is noise, and an agent that hedges on every city stops being useful.
    top_pop = top.get("population") or 0
    rivals = [describe(o) for o in results[1:4]
              if o["name"].lower() == top["name"].lower()
              and (o.get("population") or 0) >= 0.10 * top_pop]
    note = (f" NOTE: '{city}' is ambiguous — could also be {'; '.join(rivals)}. "
            f"Confirm which one before planning." if rivals else "")
    return label, top["latitude"], top["longitude"], note


# NOTE: The tools already have some docstring descriptions
# but you can modify them if you find the descriptions insufficient or inaccurate.
@tool
def get_weather(city: str, date: str = "") -> str:
    """Get the weather forecast for a city on a date (YYYY-MM-DD).

    Only the next 16 days can be forecast. For any date beyond that the forecast
    does not exist, and this tool will say so.  Say that plainly instead of
    describing what the season is usually like. Leave date empty for today.

    The city name is resolved to a real place, and this tool tells you WHICH
    place it picked. If other places share the name, it says so: check it matches
    what the user meant before you plan anything.
    """
    # TODO: implement. Return a readable string
    return "not implemented"


@tool
def find_attractions(city: str, interest: str = "") -> str:
    """Find sights, museums, parks and landmarks in a city.

    interest narrows it, e.g. "art", "history", "outdoors", "free".
    Use this for things to SEE. For food use find_restaurants; for things
    happening on a particular date use find_events.
    """
    # TODO: implement. Return a readable string
    return "not implemented"


@tool
def find_restaurants(city: str, budget: str = "") -> str:
    """Find places to eat in a city.

    budget narrows it, e.g. "cheap", "mid-range", "fine dining".
    Use this for food and drink only. It does not return opening hours or
    current prices, so do not promise either.
    """
    # TODO: implement. Return a readable string; never raise.
    return "not implemented"


@tool
def find_events(city: str, date: str = "", category: str = "") -> str:
    """Find real ticketed events in a city: concerts, sport, theatre, festivals.

    date is YYYY-MM-DD and means that day in the venue's own local time; leave
    it empty for the week ahead. Unlike the search tools this returns structured
    records: real dates, real venues, real links.

    category narrows by type. The five broad ones always work: "music", "sports",
    "arts & theatre", "film", "miscellaneous". Many narrower ones work too —
    "comedy", "rock", "jazz", "classical", "hip-hop", "country", "pop",
    "basketball", "hockey", "theatre", "musical", "dance", "family". Leave it
    empty for everything.

    But some plausible-sounding words match nothing at all ("opera", "magic"),
    and a category the API does not recognise returns ZERO EVENTS rather than an
    error — identical to a genuinely quiet weekend. Prefer a word from the list
    above, and never report "there is nothing on" from an empty filtered result
    without checking again without the filter.

    MOST EVENTS COME BACK WITH NO PRICE. The API documents a price field and
    fills it in for only a small fraction of events, under 10% in every city
    tested. "price not published" means exactly that. Do not substitute a guess,
    and do not read a missing price as free admission. A price published as 0 is
    a placeholder, not a free ticket.

    This only covers events sold through Ticketmaster. A quiet result does not
    mean nothing is happening. Say that rather than implying the city is empty.
    """
    # TODO: implement. Return a readable string.
    return "not implemented"


@tool
def get_transit_info(city: str) -> str:
    """Get general information about getting around a city: metro, bus, passes, fares.

    This returns written guidance, NOT timetables and NOT journey times. If the
    user asks how many minutes a specific trip takes, say you cannot look that
    up rather than estimating it.
    """
    # TODO: implement. Return a readable string
    return "not implemented"


