"""Metrics computed from saved records. No model calls."""
import random


def by_task(records, check):
    """For each task, the result of check(record) on each of its runs, in run order."""
    out = {}
    for r in sorted(records, key=lambda r: r["run"]):
        out.setdefault(r["task"], []).append(check(r))
    return out


def bootstrap_ci(values, n=10_000, seed=0):
    """95% interval for the mean, resampling the values (one per task) with replacement."""
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def success(passes):
    """Mean over tasks of each task's pass rate, its 95% interval, and pass^k (the share of tasks
    that passed on every run)."""
    rates = [sum(runs) / len(runs) for runs in passes.values()]
    low, high = bootstrap_ci(rates)
    pass_k = sum(all(runs) for runs in passes.values()) / len(passes)
    return sum(rates) / len(rates), low, high, pass_k


def paired_difference(passes_a, passes_b):
    """Per task, pass rate under b minus pass rate under a; the mean, its 95% interval, and the tasks
    that differ."""
    diffs = {t: sum(passes_b[t]) / len(passes_b[t]) - sum(passes_a[t]) / len(passes_a[t]) for t in passes_a}
    low, high = bootstrap_ci(list(diffs.values()))
    return sum(diffs.values()) / len(diffs), low, high, {t: d for t, d in diffs.items() if d}


def cohen_kappa(a, b):
    """Agreement between two lists of labels, corrected for the agreement expected by chance."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)                                            # e.g. {"PASS", "FAIL"}
    chances = [(a.count(l) / n) * (b.count(l) / n) for l in labels]     # one per label: both pick it by chance
    chance = sum(chances)                                               # e.g. 0.49 + 0.09 = 0.58
    if chance == 1:          # one label everywhere: kappa is undefined
        return float("nan")
    return (observed - chance) / (1 - chance)
