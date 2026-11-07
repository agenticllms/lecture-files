"""Scoring a run against the held-out tests. Given.

The team never sees eval/. The hidden tests run in a sandbox, like everything else that runs code
an agent wrote.
"""
import json
import os
import re

from . import config
from .repo import repo_files
from .sandbox import open_sandbox, upload_files

LINE = re.compile(r"^(\w+) \(test_hidden\.Issue(\d+)\w*\.\w+\) \.\.\. (ok|FAIL|ERROR)")


def load_labels():
    with open(os.path.join(config.EVAL_DIR, "labels.json")) as f:
        return {int(k): v for k, v in json.load(f).items()}


def run_tests(patches):
    """Apply patches to a copy of the repository in a sandbox and run the public and hidden tests.

    Returns {"public_ok": bool, "public_output": str, "hidden": {issue: bool}}, where an issue's
    hidden tests pass only if every test for that issue passes."""
    files = repo_files()
    for p in patches:
        files[p["path"]] = p["code"]
    hidden = open(os.path.join(config.EVAL_DIR, "hidden_tests", "test_hidden.py")).read()
    with open_sandbox() as (sandbox, workdir):
        upload_files(sandbox, files, f"{workdir}/repo")
        upload_files(sandbox, {"test_hidden.py": hidden}, f"{workdir}/eval")
        public = sandbox.execute(f"cd {workdir}/repo && python -m unittest discover -s tests 2>&1 | tail -3")
        run = sandbox.execute(f"cd {workdir}/eval && PYTHONPATH={workdir}/repo python -m unittest -v test_hidden 2>&1")
    passed = {}
    for line in run.output.splitlines():
        m = LINE.match(line.strip())
        if m:
            n = int(m.group(2))
            passed[n] = passed.get(n, True) and m.group(3) == "ok"
    return {"public_ok": public.exit_code == 0 and "OK" in public.output,
            "public_output": public.output.strip(), "hidden": passed}


def score(triage, claims, patches):
    """One row per issue, and the totals.

    triage: {issue: label} the system decided. claims: {issue: True} for each bug the system says it
    fixed (for the team, the fixes the verifier accepted). patches: the code changes to test."""
    labels = load_labels()
    triage = {int(k): v for k, v in triage.items()}     # JSON files store the issue numbers as strings
    claims = {int(k): v for k, v in claims.items()}
    tests = run_tests(patches)
    rows = []
    for n, truth in sorted(labels.items()):
        fixed = tests["hidden"].get(n, False)
        rows.append({"issue": n, "label": truth["label"], "triage": triage.get(n, "missing"),
                     "triage_ok": triage.get(n) == truth["label"], "claimed_fixed": bool(claims.get(n)),
                     "hidden_pass": fixed,
                     "false_claim": bool(claims.get(n)) and not fixed,
                     # resolved: a bug whose hidden tests pass, or a non-bug labeled correctly and left as documented
                     "resolved": fixed if truth["label"] == "bug" else (triage.get(n) == truth["label"] and fixed)})
    bugs = [r for r in rows if r["label"] == "bug"]
    others = [r for r in rows if r["label"] != "bug"]
    totals = {"resolved": sum(r["resolved"] for r in rows), "issues": len(rows),
              "triage_correct": sum(r["triage_ok"] for r in rows),
              "bugs_fixed": sum(r["hidden_pass"] for r in bugs), "bugs": len(bugs),
              "claimed_fixed": sum(r["claimed_fixed"] for r in bugs),
              "false_claims": sum(r["false_claim"] for r in rows),
              "non_bugs_unchanged": sum(r["hidden_pass"] for r in others), "non_bugs": len(others),
              "public_tests_pass": tests["public_ok"]}
    return {"rows": rows, "totals": totals, "public_output": tests["public_output"]}


def score_team(out):
    """Score a team run: the triage labels, and the fixes the verifier accepted."""
    verified = [r for r in out["results"] if r["status"] == "verified"]
    claims = {r["number"]: True for r in verified}
    return score(out["labels"], claims, [{"path": r["fix"]["path"], "code": r["fix"]["new_code"]} for r in verified])
