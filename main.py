# btc-cent-forecast-01 — wallet w10 entry (Python 3.13, standard library only).
#
# Ensemble of three, averaged, then clamped to +-1.5% of the checkpoint close:
#   (a) persistence:        last_close
#   (b) slope extrapolation: slope of the last 60 minutes x 240 minutes x 0.5
#   (c) mean reversion:     last_close + 0.10 * (median of the last 1440 closes - last_close)
# Fallback: fewer than 100 prices -> forecast = last_close.
#
# Deterministic (no randomness, no time, no network), reads every *.in in
# $MAKEFUN_INPUT_DIR (else /input/) and writes one <id>.out per case to
# $MAKEFUN_OUTPUT_DIR (else /output/).

import json
import math
import os
import statistics

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999


def price5(x):
    """Keep a guess on the grid's 5 decimals and inside (0, 10,000,000)."""
    x = min(MAX_PRICE, max(MIN_PRICE, x))
    return round(x * 100000) / 100000


def forecast(prices):
    """One forecast for one market's list of 1-minute closes."""
    if not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    if not isinstance(last, (int, float)) or not math.isfinite(last):
        raise ValueError("last price is not a finite number")
    last = float(last)
    n = len(prices)
    if n < 100:
        return price5(last)
    # Any non-finite value in the windows we use -> fall back to persistence.
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in prices[-1440:]):
        return price5(last)

    # (a) persistence
    persistence = last

    # (b) slope extrapolation: linear fit over the last 60 minutes,
    # slope per minute * 240 minutes ahead * 0.5 damping.
    window = prices[-60:]
    m = len(window)
    # least squares slope: sum((i - mean_i) * (x_i - mean_x)) / sum((i - mean_i)^2)
    mean_i = (m - 1) / 2.0
    mean_x = sum(window) / m
    num = sum((i - mean_i) * (x - mean_x) for i, x in enumerate(window))
    den = sum((i - mean_i) ** 2 for i in range(m))
    slope = num / den if den else 0.0
    slope_extrap = last + slope * 240.0 * 0.5

    # (c) mean reversion toward the median of the last 1440 closes.
    med = statistics.median(prices[-1440:])
    reversion = last + 0.10 * (med - last)

    raw = (persistence + slope_extrap + reversion) / 3.0

    # Clamp to +-1.5% of the checkpoint close.
    lo = last * 0.985
    hi = last * 1.015
    raw = min(hi, max(lo, raw))

    return price5(raw)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for fname in inputs:
        case_id = fname[: -len(".in")]
        with open(os.path.join(INPUT_DIR, fname), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{fname} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or not prices:
            raise ValueError(f"{fname} market has no prices")
        out = {"forecasts": [{"case": case_id, "price": forecast(prices)}]}
        with open(os.path.join(OUTPUT_DIR, case_id + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
