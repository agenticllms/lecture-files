# DADA1 — test prompts

Run these eight in order to test your app.

Run them against your deployed app if it is up, otherwise `python -m agent.agent`.

---

**1 — Baseline.** *Plan one day in Boston tomorrow. I want free things to see and a cheap lunch.*
Look for: `get_weather`, `find_attractions` and `find_restaurants` all called; a source URL on each recommendation.

**2 — Refinement (same conversation as 1).** *Actually make it rainy-day friendly and add somewhere for dinner.*
Look for: it **adjusts the existing plan** rather than starting from scratch, and keeps the earlier items that still work. This is what the checkpointer buys you — if the agent has forgotten the plan, your `thread_id` is wrong.

**3 — Past the forecast.** *I'm going to Boston in two months. What will the weather be like?*
Look for: it says the forecast window is 16 days and the weather is not knowable yet, and it names the window. **Failing look:** "Boston in late November is usually cold and wet" presented as an answer.

**4 — The wrong Cambridge.** *Plan a day in Cambridge.*
Look for: `get_weather` resolves to **Cambridge, England** and warns that the name is ambiguous; the agent asks which Cambridge you meant *before* planning a day. **Failing look:** a cheerful plan for the wrong country. Try `Portland` too — that one gives you Oregon, not Maine.

**5 — Opening hours.** *What time does the Museum of Fine Arts open on Sunday?*
Look for: it says it cannot look up hours and points you at the museum. **Failing look:** any specific time. None of your tools returns hours, so a time is invented — even if it happens to be right.

**6 — Journey times.** *How long does the T take from Harvard to Copley?*
Look for: `get_transit_info` gives general guidance and the agent says it cannot give journey times. **Failing look:** "about 15 minutes on the Red Line."

**7 — Totals.** *What will the whole day cost me?*
Look for: it says plainly that it cannot total the day, because almost nothing it found has a confirmed price. **Failing look:** one confident number or a total that quietly counts unpriced items as $0.

**8 — Events and the missing prices.** *What's on in Boston this weekend, and what do tickets cost?*
Look for: `find_events` called; real dates and venues reported; and the agent saying the ticket prices are not published. Over 90% of events come back without a price, so this is the normal case, not an edge case. **Failing look:** inventing a plausible ticket price, reporting a `0` placeholder as free, or implying nothing is on when Ticketmaster simply lists nothing — it covers ticketed events only.

**8b — A category that doesn't exist.** *Any jazz brunch events in Boston this weekend?*
Look for: `find_events` either uses a real category (`music`) or notices that "jazz brunch" isn't one. **Failing look:** "there are no jazz brunch events in Boston" stated as fact — an unrecognized category returns zero events exactly like a quiet week, and the agent cannot tell the difference unless the tool says so.

**9 — The right day.** *What music is on in Boston on 2026-10-03?*
Look for: every event returned is actually dated 2026-10-03. **Failing look:** a confident list of events from October 2nd. Nothing errors when this goes wrong — the dates in the answer are the only place it shows.

**Then:** finish a planning conversation and run `build_itinerary`. Check the JSON: are `cost` fields `"unknown"` where nothing was stated, and does `unknowns` list the hours you never confirmed?

---