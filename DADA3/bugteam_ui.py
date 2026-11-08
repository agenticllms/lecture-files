"""The DADA3 app: the bug-fixing team, working on issues while you watch. Given.

Two tabs.

- One issue: pick an open issue, or write one of your own, and press Fix.
- All issues: run the team on every open issue at once (or the ones you keep picked). Each bug gets
  its own pair, and the pairs run at the same time, config.MAX_PARALLEL at once. This is the
  fan-out from notebook 02: the messages of different issues interleave, and each says which issue
  it is about.

Both show, in order: triage's labels and reasoning; the fixers and the verifiers handing fixes back
and forth, as a chat, while it happens; and the maintainer's report when the run finishes. The team
is the graph from bugteam/team.py.
"""
import time

import gradio as gr

from bugteam import config, team
from bugteam.repo import load_issues
from bugteam.util import CallCounter

YOURS = "Write your own issue"


def names():
    return {f"#{i['number']} {i['title']}": i for i in load_issues()}


def issue_markdown(issues):
    return "\n\n---\n\n".join(f"**#{i['number']} {i['title']}** (opened by {i['user']})\n\n{i['body']}"
                              for i in issues)


def run_issues(issues):
    """A generator: every yield updates the triage text, the chat, the report, and the cost line."""
    counter, start = CallCounter(), time.time()
    tag = len(issues) > 1        # with several issues, every message says which one it is about
    triage, chat, report = f"Triage is reading {len(issues)} issue(s) and the code ...", [], ""
    pairs = {}          # the id LangGraph gives each pair's task -> its issue number
    working = {}        # issue number -> index in chat of its "working" line

    def fixer(n, text):
        return {"role": "user", "content": f"**{f'#{n} ' if tag else ''}Fixer:** {text}"}

    def verifier(n, text):
        return {"role": "assistant", "content": f"**{f'#{n} ' if tag else ''}Verifier:** {text}"}

    def say(n, message, then=None):
        """Put message where issue n's "working" line was, and add a new working line if given."""
        if n in working:
            chat[working.pop(n)] = message
        else:
            chat.append(message)
        if then:
            working[n] = len(chat)
            chat.append(then)

    def cost():
        return f"{counter.calls} model calls, {counter.tokens:,} tokens, {time.time() - start:.0f} s"

    yield triage, chat, report, cost()
    settings = {"max_concurrency": config.MAX_PARALLEL, "recursion_limit": 60, "callbacks": [counter]}
    for namespace, mode, chunk in team.build_graph().stream({"issues": issues}, settings,
                                                            stream_mode=["updates", "tasks"], subgraphs=True):
        if mode == "tasks":
            # A pair starting: the team's fix node, with the Send's payload as its input.
            if namespace or chunk.get("name") != "fix" or "input" not in chunk:
                continue
            n = chunk["input"]["issue"]["number"]
            pairs[chunk["id"]] = n
            say(n, fixer(n, "reading the code ..."))
            working[n] = len(chat) - 1
        elif not namespace:
            for node, update in (chunk or {}).items():
                if node == "triage":
                    labels, reasons = update["labels"], update["reasons"]
                    if tag:
                        triage = "\n".join(f"- **#{n} {label}.** {reasons[n]}" for n, label in labels.items())
                    else:
                        n, label = next(iter(labels.items()))
                        triage = f"**Triage: {label}.** {reasons[n]}"
                elif node == "report":
                    for i in sorted(working.values(), reverse=True):   # rounds that ran out
                        del chat[i]
                    working.clear()
                    report = update["report"]
        elif len(namespace) == 1:       # a pair's own nodes; deeper ones are inside the fixer or the verifier
            n = pairs.get(namespace[0].split(":", 1)[-1])
            for node, update in (chunk or {}).items():
                update = update or {}
                if node == "fixer":
                    if update.get("status") == "no_fix":
                        say(n, fixer(n, "stopped without handing over a fix."))
                    else:
                        say(n, fixer(n, update["fix"]["note"]),
                            then=verifier(n, "writing a test and running it in a sandbox ..."))
                elif node == "verifier":
                    if update.get("status") == "verified":
                        say(n, verifier(n, "accepted. " + update["evidence"]))
                    else:
                        say(n, verifier(n, "sent it back. " + update["evidence"]),
                            then=fixer(n, "correcting the fix ..."))
        else:
            continue
        yield triage, list(chat), report, cost()


# ---------------------------------------------------------------------------------- one issue
def show_one(choice):
    """Show the issue's text, or the boxes for writing one."""
    if choice == YOURS:
        return gr.update(visible=False), gr.update(visible=True)
    return gr.update(value=issue_markdown([names()[choice]]), visible=True), gr.update(visible=False)


def run_one(choice, title, body):
    if choice == YOURS:
        if not title.strip() or not body.strip():
            raise gr.Error("Give your issue a title and a description.")
        issue = {"number": 11, "title": title.strip(), "body": body.strip(), "user": "you", "labels": []}
    else:
        issue = names()[choice]
    yield from run_issues([issue])


# ---------------------------------------------------------------------------------- all issues
def run_all(choices):
    issues = [names()[c] for c in choices]
    if not issues:
        raise gr.Error("Pick at least one issue.")
    yield from run_issues(issues)


def outputs(label):
    """The four outputs of a run, in the order run_issues yields them."""
    cost = gr.Markdown()
    triage = gr.Markdown()
    chat = gr.Chatbot(label=label, height=480)
    report = gr.Markdown()
    return [triage, chat, report, cost]


def interface():
    choices = list(names())
    with gr.Blocks(title="DADA3 - Huskyutils Bug-fixing Team") as demo:
        gr.Markdown("# DADA3 - Huskyutils Bug-fixing Team\nTriage decides whether an issue is a bug. Each bug "
                    "gets a pair: the fixer writes a fix, and the verifier, a deep agent with a sandbox that is "
                    "not shown the fix, tests it and accepts it or sends it back."
                    f"\n\nChat model: `{config.model_name()}`. Sandbox: `{config.SANDBOX}`.")
        with gr.Tab("One issue"):
            one = gr.Dropdown(choices + [YOURS], value=choices[0], label="issue")
            one_text = gr.Markdown(issue_markdown([names()[choices[0]]]))
            with gr.Column(visible=False) as yours:
                title = gr.Textbox(label="title")
                body = gr.Textbox(label="what you called, what you got, and what you expected", lines=4)
            go_one = gr.Button("Fix", variant="primary")
            one_out = outputs("fixer and verifier")
            one.change(show_one, one, [one_text, yours])
            go_one.click(run_one, [one, title, body], one_out)
        with gr.Tab("All issues"):
            gr.Markdown(f"Every bug gets its own pair, and {config.MAX_PARALLEL} pairs work at the same time, "
                        "so the messages of different issues interleave. A run on all ten issues is about "
                        "60 model calls and a few minutes.")
            many = gr.Dropdown(choices, value=choices, multiselect=True, label="issues")
            go_all = gr.Button("Fix all", variant="primary")
            all_out = outputs("fixers and verifiers")
            go_all.click(run_all, many, all_out)
    return demo
