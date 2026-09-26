# DADA1: The Trip Planner Agent

---

## 1. Agent Description

In your first DADA, you will build a **trip planning agent** you can hold a conversation with. You say *"plan me a day in Boston tomorrow, free things and a cheap lunch"*; it checks the weather, finds sights, finds somewhere to eat, and gives you a plan with its sources. Then you say *"make it rainy-day friendly and add dinner"* and it adjusts the plan it already made. At the end it hands you the whole thing as a structured record.

Your five tools deliberately do **not** all work the same way. Two query structured APIs that return typed fields and sometimes return a documented field empty. Three are web searches that hand back prose someone wrote, with no guarantee it is current. They fail differently, and a good agent keeps track of which kind just answered it.


---

## 2. Setup

Get the files the same way as every class day: pull, then work in a copy:

```bash
cd lecture-files
git pull
cd ..
cp -r lecture-files/DADA1 DADA1     # work in the copy, not in lecture-files/
cd DADA1
```

You will need to add three keys to your .env file:

1. `GOOGLE_API_KEY` - you may use another vendor such as OpenRouter or NVIDIA
2. `TAVILY_API_KEY` — free at [tavily.com](https://tavily.com), same one as W02b.2.
3. `TICKETMASTER_API_KEY` — free at [developer.ticketmaster.com](https://developer.ticketmaster.com/products-and-docs/apis/getting-started/). Register, and the key works immediately: 5,000 calls/day.

The weather and geocoding APIs ([Open-Meteo](https://open-meteo.com/en/docs)) need **no key**.

```bash
cd trip_planner
pip install -r requirements.txt # this is optional if your project is already set up
python -m agent.agent        # chat in the terminal
python app.py                # the web UI, http://127.0.0.1:7860
```

Never commit your `.env` file.

---

## 3. What you're given

```
trip_planner/
  agent/tools.py       STUB — five tool signatures with docstrings; you write the bodies
                       (the _search helper is written for you)
  agent/prompts.py     STUB — you write the system prompt
  agent/itinerary.py   STUB — the Activity model is written as an example; you write
                       DayPlan, Itinerary, and build_itinerary
  agent/agent.py       STUB — you build the agent with memory
  agentui.py           COMPLETE — the same chat UI from W03
  app.py               COMPLETE — the entry point Render runs
test_prompts.md        the eight prompts you must run
```

---

## 4. The Tools

| Tool | API | What it does |
|---|---|---|
| `get_weather(city, date)` | Open-Meteo | Geocode the city, then forecast. **16 days** |
| `find_attractions(city, interest)` | Tavily | Sights, museums, parks |
| `find_restaurants(city, budget)` | Tavily | Food |
| `find_events(city, date, category)` | Ticketmaster | Ticketed events: **real dates and venues**, rarely a price |
| `get_transit_info(city)` | Tavily | How to get around — guidance, not timetables |

Three of them call the same `_search` helper, which is written for you, so their bodies are two or three lines each. **The part that matters is the docstring and the query you build.** The model reads the docstrings to decide which tool to call: if `find_attractions` and `find_restaurants` describe themselves vaguely, it will call the wrong one, and no amount of prompt-writing will fix a tool that lies about what it does.

**`get_weather`** involves two requests. `_geocode` is written for you: it turns a city name into coordinates and warns you when the name is ambiguous. You write the forecast half. To this end, read the [Open-Meteo docs](https://open-meteo.com/en/docs), request the `daily` fields you need, and find the one thing that matters most in the response: **which dates it actually returned.** Ask for a date outside that window and there is nothing there, so your tool must say what the window *is*.

Carry the geocoder's warning into your return string. `Cambridge` resolves to **Cambridge, England**, which is more populous than Cambridge, Massachusetts, so it ranks first. `Portland` gives you Oregon, not Maine. Please note that neither is an error. Both are confident answers about the wrong place, and the agent can only notice if your tool tells it.

**`find_events`** is the other structured one. Read the [Ticketmaster Discovery docs](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/) and dig the event name, date, venue and `priceRanges` out of `_embedded.events[]`.

Then study what you actually get. The docs describe `priceRanges` clearly, and **fewer than one event in ten has it** — 1 of 50 in Boston, 0 of 50 in Las Vegas, 4 of 50 in Chicago. Requesting the individual event by id does not help. When it *is* present it is sometimes `0.0–0.0`, which is a seller placeholder and emphatically not free admission.

**A documented field is not a populated field, and you only find that out by calling the API.** This is the most useful thing in the assignment, and no amount of reading the docs would have told you. Your tool has to say "price not published" and mean it; your agent must not turn that into a guess, a zero, or "free".

There is a third thing in this API worth your attention, and it is the one most likely to get you. Ticketmaster has **two** date-filter pairs. `startDateTime`/`endDateTime` take a trailing `Z` and are read as **UTC**; `localStartDateTime`/`localEndDateTime` take no `Z` and use the **venue's local time**. Ask for October 3 in Boston with the UTC pair and your window opens at 8pm on October 2 — right as that evening's concerts start — so you get a page of October 2 events and none from the day you asked about. The request succeeds. The JSON is well formed. It is simply about the wrong day.

Use the local pair, and make your window one day when the user names one day.

The `category` argument narrows by type — `music`, `sports`, `arts & theatre`, `film`, `miscellaneous`. There is a second trap in it: **a category the API does not recognise returns zero events rather than an error.** `classificationName=banana` is a clean, empty, successful response, and it looks exactly like a city with nothing on. Your tool should not let the agent report an empty weekend without flagging that possibility.

Two rules for all five, the same as the Husky Tech agent:

**Return a readable string, never raise.** `return f"No forecast for {date} — only ... are available."` is something the model can act on. A traceback is not.

**Say what you don't have.** Your search tool returns snippets with no opening hours in them. If its return value doesn't mention that, the model will fill the gap itself.

---

## 5. The itinerary

`build_itinerary(model, result)` is `file_ticket` from W03b.1, pointed at a trip: transcript in, typed record out. You write `DayPlan` and `Itinerary` around the `Activity` model that's already there. An itinerary is a list of days, each holding a list of activities.

One field is worth thinking about. `Activity.cost` is a **string**, not a number, so `"unknown"` is something the itinerary can say. If you make it a `float`, the model will likely have to invent a figure to fill it. Your `Itinerary` needs an `unknowns` list for the same reason.

---

## 6. Required behaviors

These are what's actually graded, and `test_prompts.md` is where you demonstrate them.

**B1 · Right tool, right question.** Weather questions reach `get_weather`, food questions reach `find_restaurants`. This is a docstring problem, not a prompt problem.

**B2 · Honest about the edges.** No forecast past 16 days. No opening hours, ever — none of your tools return them. No journey times. Almost no prices: search snippets rarely state one and Ticketmaster rarely publishes one. **The obvious answer being probably true is not the same as your tools supporting it.**

**B2b · Absent is not zero.** A missing price is not free, and a published `0` is not free either. Most of your itinerary's costs will read `unknown`, and that is the correct result. An itinerary full of confident numbers is the failure, not the goal.

**B3 · Sources.** Every recommendation names the URL it came from.

**B4 · Memory.** "Make it cheaper" adjusts the existing plan. If your agent starts over, check your `thread_id`.

**Run the eight prompts in `test_prompts.md` to test your app.**

---

## 7. App Deployment

Render deploys from a GitHub repository, so first put your `DADA1` copy into one of your own, not `lecture-files`, which is shared and read-only:

```bash
cd DADA1
git init
git add .
git status                   # check that .env is NOT in this list
git commit -m "DADA1 trip planner agent"
```

Then create an empty repo on GitHub and push to it. **Create it as private.** Render deploys from private repos and Gradescope submits from them, and a public repo containing your solution is an academic-integrity violation - during the course and after it. If you want to show this work to an employer later, ask me first.

Check `git status` before you commit: a key that reaches GitHub stays in the history even after you delete the file.

Now deploy to [Render](https://render.com) as a **Web Service** on the free tier:

- **Root Directory:** `trip_planner` - the app sits one level down, and Render looks in the repo root unless you tell it otherwise. This is the most common first-deploy failure: Render reports it cannot find `requirements.txt`.
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python app.py`
- **Environment variables:** `GOOGLE_API_KEY` (or your specific vendor), `TAVILY_API_KEY` **and `TICKETMASTER_API_KEY`**, set in Render's dashboard. **Not in the repo.** If you miss the third one, the app will deploy fine and then tell every user that events are unavailable.

`app.py` already binds to `0.0.0.0` on Render's `$PORT`, which is the only code difference from running locally. The free tier sleeps after inactivity, so the first request takes ~30 seconds. Therefore, you'll need to keep your deployment active by sending it a few requests every day until it's graded.

The page is the given chat UI plus one button: **Build itinerary from this conversation**, which runs your `build_itinerary` and shows the JSON underneath. That button is how your structured output gets graded, so make sure it works on the deployed site and not just in the terminal.

UI polish is worth nothing here. The UI is given to you.

---

## 8. Submission

You will submit your project on Gradescope, using the **GitHub** integration rather than uploading files. To this end, creat a new **private** repo for the assignment, and when submitting on Gradescope, select your repo and branch.

The first time you use the GitHub integration on Gradescop, GitHub will ask you to authorize Gradescope. On that screen, under **Repositories**, choose **"Public and private"**. The default is public-only, and if you accept it your private repo simply will not appear in Gradescope's list - with nothing to tell you why. If that happens, go to [github.com/settings/applications](https://github.com/settings/applications), click Gradescope, and grant access.

Before you submit, fill in the line at the top of your `README.md`:

```
Deployed app: <your Render URL>
```

That is how your running app gets found and graded. Gradescope takes a snapshot of the repo at submission time, so pushing after the deadline changes nothing.

It's of great importance that you make sure the repo is private. You should not make the repo public at any point.

---

### Extra credit — a tool that calls a tool

`find_events` searches by city. It will not reliably tell you whether a *specific*
act is playing while your user is in town, because the answer may be on page four.

Ticketmaster answers that with two requests, and the chain is the point:

1. **Attraction Search** (`/discovery/v2/attractions`) finds the act and returns its
   `id`. An "attraction" in this API is a **performer, team or touring show** — the
   Celtics, the Bruins, *Wicked* — not a place.
2. **Event Search** with `attractionId=<that id>` plus your city and dates returns
   when and where they play.

Write `find_performer_events(performer: str, city: str, date: str = "")` that does
both and returns a readable string. Full marks need it to handle the cases that
make chained tools hard: **no such performer** (say so, don't guess an id), **the
performer exists but has nothing in that city** (a real and different answer), and
**an ambiguous name** where several acts match — "Boston" matches the Celtics, the
Bruins, Boston College and a band called Boston Manor, and picking the first one
silently is the same mistake `get_weather` warns you about.

One warning, because the name will mislead you: **Ticketmaster attractions are not
tourist attractions.** Searching them for "museum" returns *Balloon Museum* and
*Twist Museum* — touring ticketed exhibitions — not the Museum of Fine Arts. This
endpoint cannot replace `find_attractions`.


---

## 9. Getting started

1. **Write `get_weather` first, and print the raw JSON before you parse it.** Call it on `"Boston"`, then on `"Cambridge"`, then on a date two months out. Those three calls contain most of this assignment.
2. **Then the four search tools**, and test each one directly — `print(find_restaurants.invoke({"city": "Boston", "budget": "cheap"}))` — before you give any of them to the agent. Most agent bugs are tool bugs. Study the APIs carefully.
3. **Write the system prompt last.** Run the eight test prompts with a one-line prompt first, see what breaks, then write the prompt that fixes it. A prompt written before you've seen a failure fixes an imaginary one.
4. **Deploy early, not on Saturday.** A deploy that works on Thursday is a deploy you can debug.

**Office hours:** bring your prompt log, not "it doesn't work."

---

## 10. Using AI assistance

You may use a coding agent on this assignment. You are building one; pretending you
would not use one would be strange.

The bundle includes an **`AGENTS.md`** file. Claude Code, Cursor, Copilot and most
other coding agents read it automatically when it sits at the root of the folder
you have open, so keep it where it is and open `DADA1/` as your project. It tells
the agent to work as a tutor rather than an author.

**What it asks the agent to do**

- Send you to the lecture notebooks first. Almost everything mechanical here —
  `@tool`, `create_agent`, `InMemorySaver`, `with_structured_output` — you already
  built in W02b and W03a/b, and those notebooks are public at
  [github.com/agenticllms/lecture-files](https://github.com/agenticllms/lecture-files).
  An agent that re-explains W03a.2 from scratch is wasting your time and cutting
  you off from your own course.
- Explain the APIs properly. Reading what Open-Meteo, Tavily and Ticketmaster
  actually return is most of this assignment, and getting help with it is fine.
- Explain code step by step, in pieces you write yourself.

**What it asks the agent not to do**

Write the code fully for you.
