"""Run the agent on the task set and save one record per run.

    python run_eval.py --model gpt-4.1-mini --condition policy --runs 5
    python run_eval.py --model gpt-4.1-mini --condition check --runs 5
    python run_eval.py --model gpt-4.1-mini --condition check --runs 1 --tasks t14,t16

Records go to results/<model>/<condition>.jsonl. Running the same command again resumes: runs already
in the file are skipped.
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from app.agent import load_model
from evals.conditions import CONDITIONS, tasks
from evals.runner import run_condition


def results_folder(model_name):
    """results/gpt-4.1-mini for "gpt-4.1-mini", results/qwen3.5-9b for "ollama:qwen3.5:9b"."""
    return Path("results") / model_name.split(":", 1)[-1].replace(":", "-").replace("/", "-")


def main():
    parser = argparse.ArgumentParser(description="Run the support agent on the evaluation tasks.")
    parser.add_argument("--model", required=True, help='for example "gpt-4.1-mini" or "ollama:qwen3.5:9b"')
    parser.add_argument("--condition", required=True, choices=list(CONDITIONS))
    parser.add_argument("--runs", type=int, default=5, help="runs of each task")
    parser.add_argument("--tasks", help="comma-separated task ids; all tasks if left out")
    parser.add_argument("--pause", type=float, default=0, help="seconds to wait between runs, for rate limits")
    args = parser.parse_args()

    task_set = tasks()
    if args.tasks:
        keep = set(args.tasks.split(","))
        task_set = [t for t in task_set if t["id"] in keep]

    path = results_folder(args.model) / f"{args.condition}.jsonl"
    run_condition(load_model(args.model), args.condition, CONDITIONS[args.condition], task_set, args.runs,
                  path, args.pause)
    print(f"records in {path}")


if __name__ == "__main__":
    load_dotenv()
    main()
