"""The DADA3 app: the bug-fixing team, working on one issue while you watch. Given.

Pick an open issue, or write one of your own, and press Fix. The page shows, in order:

1. triage's label and reasoning
2. the fixer and the verifier handing the fix back and forth, as a chat, while it happens
3. the maintainer's report for this run, when the run finishes

The team is the graph from bugteam/team.py, run on the one issue.
"""
import time

import gradio as gr

from bugteam import config, team
from bugteam.repo import load_issues
from bugteam.util import CallCounter

YOURS = "Write your own issue"


def issue_choices():
    return [f"#{i['number']} {i['title']}" for i in load_issues()] + [YOURS]


def picked_issue(choice):
    for i in load_issues():
        if choice == f"#{i['number']} {i['title']}":
            return i
    return None


def show_issue(choice):
    """Show the issue's text, or the boxes for writing one."""
    issue = picked_issue(choice)
    if issue is None:
        return gr.update(visible=False), gr.update(visible=True)
    text = f"**#{issue['number']} {issue['title']}** (opened by {issue['user']})\n\n{issue['body']}"
    return gr.update(value=text, visible=True), gr.update(visible=False)


def fixer_says(text):
    return {"role": "user", "content": f"**Fixer:** {text}"}


def verifier_says(text):
    return {"role": "assistant", "content": f"**Verifier:** {text}"}


def run(choice, title, body):
    """A generator: every yield updates the triage line, the chat, the report, and the cost line."""
    issue = picked_issue(choice)
    if issue is None:
        if not title.strip() or not body.strip():
            raise gr.Error("Give your issue a title and a description.")
        issue = {"number": 11, "title": title.strip(), "body": body.strip(), "user": "you", "labels": []}

    counter, start = CallCounter(), time.time()
    triage, chat, report = "Triage is reading the issue and the code ...", [], ""

    def cost():
        return f"{counter.calls} model calls, {counter.tokens:,} tokens, {time.time() - start:.0f} s"

    yield triage, chat, report, cost()
    settings = {"max_concurrency": config.MAX_PARALLEL, "recursion_limit": 60, "callbacks": [counter]}
    for namespace, change in team.build_graph().stream({"issues": [issue]}, settings,
                                                       stream_mode="updates", subgraphs=True):
        if len(namespace) > 1:          # inside the fixer's or the verifier's own loop
            continue
        for node, update in (change or {}).items():
            update = update or {}
            if node == "triage":
                label = update["labels"][issue["number"]]
                triage = f"**Triage: {label}.** {update['reasons'][issue['number']]}"
                if label == "bug":
                    chat = [fixer_says("reading the code ...")]
            elif node == "fixer":
                chat = chat[:-1]        # drop the "working" line
                if update.get("status") == "no_fix":
                    chat.append(fixer_says("stopped without handing over a fix."))
                else:
                    chat += [fixer_says(update["fix"]["note"]),
                             verifier_says("writing a test and running it in a sandbox ...")]
            elif node == "verifier":
                chat = chat[:-1]
                if update.get("status") == "verified":
                    chat.append(verifier_says("accepted. " + update["evidence"]))
                else:
                    chat += [verifier_says("sent it back. " + update["evidence"]),
                             fixer_says("correcting the fix ...")]
            elif node == "report":
                if chat and chat[-1]["content"].endswith("..."):    # the rounds ran out
                    chat = chat[:-1]
                report = update["report"]
        yield triage, chat, report, cost()


def interface():
    with gr.Blocks(title="DADA3 - Huskyutils Bug-fixing Team") as demo:
        gr.Markdown("# DADA3 - Huskyutils Bug-fixing Team\nPick an open issue and press **Fix**. Triage decides "
                    "whether it is a bug. If it is, the fixer writes a fix, and the verifier, a deep agent "
                    "with a sandbox that is not shown the fix, tests it and accepts it or sends it back. "
                    f"\n\nChat model: `{config.model_name()}`. Sandbox: `{config.SANDBOX}`.")
        choice = gr.Dropdown(issue_choices(), value=issue_choices()[0], label="issue")
        first = picked_issue(issue_choices()[0])
        issue_text = gr.Markdown(f"**#{first['number']} {first['title']}** (opened by {first['user']})\n\n{first['body']}")
        with gr.Column(visible=False) as yours:
            title = gr.Textbox(label="title")
            body = gr.Textbox(label="what you called, what you got, and what you expected", lines=4)
        go = gr.Button("Fix", variant="primary")
        cost = gr.Markdown()
        triage = gr.Markdown()
        chat = gr.Chatbot(label="fixer and verifier", height=420)
        report = gr.Markdown()
        choice.change(show_issue, choice, [issue_text, yours])
        go.click(run, [choice, title, body], [triage, chat, report, cost])
    return demo
