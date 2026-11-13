"""The LLM judge for the reply, and the check of the judge against human labels."""
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from evals.metrics import cohen_kappa

CRITERIA = ["reason", "grounded", "action_matches"]


class Verdict(BaseModel):
    explanation: str = Field(description="Two or three sentences on how the reply meets or misses each criterion.")
    reason: bool = Field(description="The reply states the policy rule that decided each request in the message.")
    grounded: bool = Field(description="Every order fact in the reply matches the evidence, and it promises nothing the evidence does not support.")
    action_matches: bool = Field(description="What the reply says was done matches the tool calls in the evidence.")


JUDGE_PROMPT = """You grade replies from a customer-support agent against a rubric.

You see the customer's message, the evidence (every tool the agent called and what it returned), and the
agent's reply. Judge only from what you are shown.

- reason: the reply states the policy rule that decided each request in the message, for example that an
  order is past the 30-day window, or that a refund over $300 needs a person.
- grounded: every order fact in the reply (dates, number of days, prices, status) matches the evidence, and
  the reply makes no promise the evidence does not support, such as when money will arrive.
- action_matches: what the reply says was done (refunded, escalated, declined) matches the tool calls in
  the evidence.

Write the explanation first, then the three verdicts."""


def judge_reply(judge, message, reply, evidence):
    """Grade one reply. `judge` is a chat model."""
    grader = judge.with_structured_output(Verdict, method="json_schema")
    content = f"Customer message:\n{message}\n\nEvidence:\n{evidence}\n\nAgent reply:\n{reply}"
    return grader.invoke([SystemMessage(content=JUDGE_PROMPT), HumanMessage(content=content)])


def validate(judge, labeled):
    """Run the judge on replies people have labeled. For each criterion, return the agreement, kappa,
    and the judge's precision and recall on failures (a failure is a reply labeled False)."""
    verdicts = [judge_reply(judge, c["message"], c["reply"], c["evidence"]) for c in labeled]
    report = {}
    for k in CRITERIA:
        human = [c["labels"][k] for c in labeled]
        judged = [getattr(v, k) for v in verdicts]
        caught = sum(not h and not j for h, j in zip(human, judged))
        flagged, failures = judged.count(False), human.count(False)
        report[k] = {"agreement": sum(h == j for h, j in zip(human, judged)) / len(labeled),
                     "kappa": cohen_kappa(human, judged),
                     "precision": caught / flagged if flagged else None,
                     "recall": caught / failures if failures else None}
    return report, verdicts
