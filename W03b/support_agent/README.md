# Husky Tech Support Agent — from notebook to project

Notebooks are where you figure out what works. Projects are what you deploy.
In this exercise you move the working code from `W03b.1_CustomerSupport_Agent.ipynb`
into this folder, cell by cell, and end up with an application you can run
without Jupyter anywhere in sight.

## The transfer map

| Notebook section | Goes into | What |
|---|---|---|
| §1 The scenario and the data | `agent/tools.py` | ORDERS, RETURN_POLICY_DAYS, FAQ (+ ESCALATIONS) |
| §2 The tools | `agent/tools.py` | the four @tool functions, then the TOOLS list |
| §3 The system prompt | `agent/prompts.py` | SYSTEM_PROMPT |
| §4 Assemble the agent | `agent/agent.py` | the create_agent(...) call |
| §7 File the ticket | `agent/records.py` | TicketRecord and file_ticket — note: model becomes a parameter |
| §8 Chat loop | already in `agent/agent.py` | compare it with the notebook version |
| §10 Chat window | already in `app.py` | nothing to transfer |

Cells you do NOT transfer: the test drives (§5, §6) and the model-setup
alternatives (§0). Tests and experiments stay in notebooks; only the working
pieces graduate into files. That split — explore in a notebook, ship in files —
is the workflow, not a one-off.

## Run it

```bash
python -m agent.agent     # command-line chat; 'quit' files the ticket
python app.py             # the Gradio chat window
```

Your `.env` is found automatically (the project sits inside your course
folder, and load_dotenv searches upward). `agentui.py` must sit next to
`app.py` — copy it from the W03b folder if it is not already here.

## Why this layout

One file per responsibility: tools (what the agent can do), prompts (what it
should do), records (what it leaves behind), agent (wiring), app (how the
world reaches it). This is the same layout DADA1 hands you next week — after
today, its skeleton will look familiar.
