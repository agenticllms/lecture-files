"""Run the agent on tasks and save one record per run. Nothing here scores anything."""
import json
import time

from langchain.messages import HumanMessage

from app import store
from app.agent import build_agent


def evidence_of(messages):
    """Every tool call in a run and what it returned, one per line."""
    results = {m.tool_call_id: m.text for m in messages if m.type == "tool"}
    lines = []
    for m in messages:
        if m.type == "ai":
            for call in m.tool_calls:
                lines.append(f"{call['name']}({call['args']}) -> {results.get(call['id'], '(no result)')}")
    return "\n".join(lines) or "(no tool calls)"


def run_task(agent, task, config=None):
    """Run one task from a fresh store and return a record of what happened."""
    store.reset()
    start = time.time()
    out = agent.invoke({"messages": [HumanMessage(content=task["message"])]}, config or {})
    messages = out["messages"]
    calls, step = [], 0
    for m in messages:
        if m.type == "ai":
            step += 1
            calls += [{"step": step, "name": c["name"], "args": c["args"]} for c in m.tool_calls]
    return {
        "task": task["id"],
        "refunds": sorted(store.env["refunds"]),
        "escalated": bool(store.env["escalations"]),
        "reply": messages[-1].text,
        "calls": calls,
        "evidence": evidence_of(messages),
        "tokens": sum(m.usage_metadata["total_tokens"] for m in messages if getattr(m, "usage_metadata", None)),
        "seconds": round(time.time() - start, 1),
    }


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run_condition(model, name, prompt, tasks, n_runs, path, pause=0):
    """Run every task n_runs times and append each record to path as soon as it finishes.
    Runs already in the file are skipped, so an interrupted experiment resumes where it stopped."""
    path.parent.mkdir(parents=True, exist_ok=True)
    done = {(r["task"], r["run"]) for r in load(path)}
    agent = build_agent(model, prompt)
    for run in range(n_runs):
        for task in tasks:
            if (task["id"], run) in done:
                continue
            record = run_task(agent, task, config={"run_name": f"{name} {task['id']} run {run}",
                                                   "tags": [name], "metadata": {"task": task["id"]}})
            record.update(condition=name, run=run)
            with open(path, "a") as f:
                f.write(json.dumps(record) + "\n")
            time.sleep(pause)
        print(f"{name}: run {run} done")
