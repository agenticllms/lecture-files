"""Score saved records. No model calls, so it can be run again whenever a check changes.

    python score_eval.py results/gpt-4.1-mini

Prints, for each condition: the success rate with its 95% interval, pass^k, the trajectory check,
the judge's criteria (if the replies were judged), and the cost. Then compares each condition with the
baseline, the first condition in evals/conditions.py, task by task. Writes every failed run to
failures.csv in the same folder, for failure coding.
"""
import argparse
import csv
from pathlib import Path

from evals.checks import check_outcome, check_trajectory
from evals.conditions import CONDITIONS, tasks
from evals.judge import CRITERIA
from evals.metrics import by_task, paired_difference, success
from evals.runner import load


def main():
    parser = argparse.ArgumentParser(description="Score the saved records in a results folder.")
    parser.add_argument("folder", help="for example results/gpt-4.1-mini")
    folder = Path(parser.parse_args().folder)

    task_by_id = {t["id"]: t for t in tasks()}
    results = {name: load(folder / f"{name}.jsonl") for name in CONDITIONS}
    results = {name: records for name, records in results.items() if records}
    if not results:
        raise SystemExit(f"No records in {folder}. Run run_eval.py first.")

    outcome = lambda r: check_outcome(task_by_id[r["task"]], r)[0]
    passes = {name: by_task(records, outcome) for name, records in results.items()}

    print(f"{'condition':10}{'runs':>6}{'success':>9}{'95% CI':>16}{'pass^k':>8}{'trajectory':>12}"
          f"{'tokens/run':>12}{'s/run':>7}")
    for name, records in results.items():
        rate, low, high, pass_k = success(passes[name])
        trajectory = sum(check_trajectory(r)[0] for r in records) / len(records)
        tokens = sum(r["tokens"] for r in records) / len(records)
        seconds = sum(r["seconds"] for r in records) / len(records)
        print(f"{name:10}{len(records):>6}{rate:>9.2f}    [{low:.2f}, {high:.2f}]{pass_k:>8.2f}{trajectory:>12.2f}"
              f"{tokens:>12.0f}{seconds:>7.1f}")

    for name in results:
        verdicts = load(folder / f"{name}.verdicts.jsonl")
        if verdicts:
            shares = ", ".join(f"{k} {sum(v[k] for v in verdicts) / len(verdicts):.2f}" for k in CRITERIA)
            print(f"judge on {name} ({len(verdicts)} replies): {shares}")

    baseline = next(iter(results))
    for name in list(results)[1:]:
        mean, low, high, differ = paired_difference(passes[baseline], passes[name])
        print(f"{name} minus {baseline}: {mean:+.3f}   95% CI [{low:+.3f}, {high:+.3f}]   "
              f"tasks that differ: {', '.join(f'{t} {d:+.1f}' for t, d in differ.items()) or 'none'}")

    failures = [{"condition": name, "task": r["task"], "run": r["run"],
                 "problem": check_outcome(task_by_id[r["task"]], r)[1], "reply": r["reply"],
                 "evidence": r["evidence"], "code_a": "", "code_b": ""}
                for name, records in results.items() for r in records if not outcome(r)]
    with open(folder / "failures.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(failures[0]) if failures else ["condition"])
        writer.writeheader()
        writer.writerows(failures)
    print(f"{len(failures)} failed runs written to {folder / 'failures.csv'}")


if __name__ == "__main__":
    main()
