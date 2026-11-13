"""Check the judge against human labels, then judge the replies in saved records.

    python judge_eval.py --judge claude-haiku-5-5 --validate
    python judge_eval.py --judge claude-haiku-5-5 results/gpt-4.1-mini/policy.jsonl

Validate first. Use the judge's verdicts only for the criteria where it agrees with the labels.
Verdicts go next to the records, in <condition>.verdicts.jsonl.
"""
import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from app.agent import load_model
from evals.conditions import judge_labels, tasks
from evals.judge import CRITERIA, judge_reply, validate
from evals.runner import load


def show_validation(judge):
    labeled = judge_labels()
    report, _ = validate(judge, labeled)
    fmt = lambda x: "  n/a" if x is None else f"{x:5.2f}"
    print(f"{len(labeled)} labeled replies")
    print(f"{'criterion':16}{'agreement':>10}{'kappa':>7}{'precision':>11}{'recall':>8}")
    for k, r in report.items():
        print(f"{k:16}{r['agreement']:>10.2f}{fmt(r['kappa']):>7}{fmt(r['precision']):>11}{fmt(r['recall']):>8}")


def judge_records(judge, path):
    """Judge every saved run that has no verdict yet, and append the verdicts."""
    messages = {t["id"]: t["message"] for t in tasks()}
    out = path.with_name(path.stem + ".verdicts.jsonl")
    done = {(v["task"], v["run"]) for v in load(out)}
    todo = [r for r in load(path) if (r["task"], r["run"]) not in done]
    for r in todo:
        v = judge_reply(judge, messages[r["task"]], r["reply"], r["evidence"])
        with open(out, "a") as f:
            f.write(json.dumps({"task": r["task"], "run": r["run"], **v.model_dump()}) + "\n")
    print(f"judged {len(todo)} replies; verdicts in {out}")


def main():
    parser = argparse.ArgumentParser(description="Validate the judge, or judge the replies in saved records.")
    parser.add_argument("--judge", required=True, help='the judge model, for example "claude-haiku-5-5"')
    parser.add_argument("--validate", action="store_true", help="compare the judge with the human labels")
    parser.add_argument("records", nargs="?", help="a results file such as results/gpt-4.1-mini/policy.jsonl")
    args = parser.parse_args()

    judge = load_model(args.judge)
    if args.validate:
        show_validation(judge)
    if args.records:
        judge_records(judge, Path(args.records))
    if not args.validate and not args.records:
        parser.error("give --validate, a records file, or both")


if __name__ == "__main__":
    load_dotenv()
    main()
