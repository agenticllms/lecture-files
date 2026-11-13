# Husky Tech Support: the app and its evaluation suite

This is the Husky Tech support agent from W10a and W10b, packaged the way a project is handed in: the application customers use, and the evaluation suite that tests it, in one repository.

```
husky_support/
├── app/                    the application
│   ├── store.py            orders, policy, and the agent's tools
│   ├── agent.py            build_agent: the Week 4 loop
│   └── ui.py               the chat interface
├── evals/                  the evaluation suite
│   ├── conditions.py       the conditions, and loading the data
│   ├── runner.py           run the agent on a task and save a record
│   ├── checks.py           outcome and trajectory checks
│   ├── judge.py            the LLM judge, and its check against human labels
│   ├── metrics.py          success rate, pass^k, intervals, kappa
│   └── data/               tasks.json, judge_labels.json
├── tests/test_checks.py    tests for the checks
├── run_app.py              start the app
├── run_eval.py             run the agent on the tasks, save the records
├── judge_eval.py           validate the judge, then judge saved replies
├── score_eval.py           score saved records (no model calls)
└── results/<model>/        one .jsonl file of records per condition
```

## Three rules behind this layout

1. **The evaluation tests the app's own code.** `evals/runner.py` imports `build_agent` from `app/agent.py`, the same function `app/ui.py` uses. There is no second copy of the agent to drift out of date. The app never imports anything from `evals`.
2. **Running and scoring are separate.** `run_eval.py` saves one record per run and scores nothing. `score_eval.py` reads the records and makes no model calls. When you fix a check, you rescore the saved runs in seconds instead of running the agent again.
3. **A condition is a setting.** The conditions live in one dictionary in `evals/conditions.py`, and every script takes the condition by name.

## Running it

Put your keys in `.env` (see `example.env`), then run these from this folder.

```bash
python run_app.py                                                   # the app, at http://localhost:7860

python run_eval.py --model gpt-4.1-mini --condition policy --runs 5   # the experiment
python run_eval.py --model gpt-4.1-mini --condition check --runs 5

python judge_eval.py --judge claude-haiku-5-5 --validate              # check the judge first
python judge_eval.py --judge claude-haiku-5-5 results/gpt-4.1-mini/policy.jsonl

python score_eval.py results/gpt-4.1-mini                             # the numbers

python -m pytest tests                                                # check the checks
```

`results/gpt-4.1-mini/` already holds our 160 runs from W10b, so `score_eval.py` works before you run anything. Other models: `--model claude-haiku-5-5`, `--model google_genai:gemini-3.5-flash-lite`, or `--model ollama:qwen3.5:9b`. On the Gemini free tier, add `--pause 4`.

## For your FP3

Your project needs the same parts, with your own agent in `app/` and your own tasks, checks, and metrics in `evals/`. Keep the three rules: the evaluation imports your app, every run is saved before it is scored, and a condition is a setting. To deploy the app, use `python run_app.py` as the start command and set the `PORT` and `MODEL` environment variables on the host.
