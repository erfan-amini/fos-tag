"""The small amount of statistics the activities need."""
from __future__ import annotations

import math


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    """Sample standard deviation (n - 1)."""
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def summary(xs) -> dict:
    """n, mean, SD, SE and the 95% interval as mean +/- 2 SE, the way the course teaches it."""
    xs = [float(x) for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    n = len(xs)
    m = mean(xs)
    s = sd(xs)
    se = s / math.sqrt(n) if n >= 2 else float("nan")
    return {"n": n, "mean": m, "sd": s, "se": se, "lo": m - 2 * se, "hi": m + 2 * se,
            "min": min(xs) if xs else float("nan"), "max": max(xs) if xs else float("nan")}


def overlap(a: dict, b: dict) -> bool | None:
    """Do two 95% intervals overlap? None when either is undefined."""
    if any(math.isnan(v) for v in (a["lo"], a["hi"], b["lo"], b["hi"])):
        return None
    return not (a["hi"] < b["lo"] or b["hi"] < a["lo"])


def nice_bin(lo: float, hi: float, target: int = 14) -> float:
    """A bin width from a short list of round numbers, giving about `target` bins."""
    span = max(hi - lo, 1e-9)
    raw = span / target
    for w in (0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100):
        if w >= raw:
            return w
    return 100.0


def dot_stack(values, width: float):
    """Positions for a dot histogram: (x at bin centre, level 1..k) for each value, in input order."""
    counts: dict[int, int] = {}
    out = []
    for v in values:
        b = math.floor(v / width + 1e-9)
        counts[b] = counts.get(b, 0) + 1
        out.append(((b + 0.5) * width, counts[b]))
    return out


def fit_through_origin(xs, ys) -> dict:
    """Least squares for y = k x. Also R^2 against the mean of y, and n."""
    pts = [(float(x), float(y)) for x, y in zip(xs, ys)]
    n = len(pts)
    sxx = sum(x * x for x, _ in pts)
    if n == 0 or sxx == 0:
        return {"k": float("nan"), "r2": float("nan"), "n": n}
    k = sum(x * y for x, y in pts) / sxx
    ybar = sum(y for _, y in pts) / n
    ss_res = sum((y - k * x) ** 2 for x, y in pts)
    ss_tot = sum((y - ybar) ** 2 for _, y in pts)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"k": k, "r2": r2, "n": n}


def fit_line(xs, ys) -> dict:
    """Ordinary least squares y = a + b x."""
    pts = [(float(x), float(y)) for x, y in zip(xs, ys)]
    n = len(pts)
    if n < 2:
        return {"a": float("nan"), "b": float("nan"), "r2": float("nan"), "n": n}
    xbar = sum(x for x, _ in pts) / n
    ybar = sum(y for _, y in pts) / n
    sxx = sum((x - xbar) ** 2 for x, _ in pts)
    if sxx == 0:
        return {"a": float("nan"), "b": float("nan"), "r2": float("nan"), "n": n}
    b = sum((x - xbar) * (y - ybar) for x, y in pts) / sxx
    a = ybar - b * xbar
    ss_res = sum((y - a - b * x) ** 2 for x, y in pts)
    ss_tot = sum((y - ybar) ** 2 for _, y in pts)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"a": a, "b": b, "r2": r2, "n": n}


def fmt(x: float, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{nd}f}"
