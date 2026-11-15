# btc-cent-forecast-01 — wallet w10

Forecast Bitcoin's price 240 minutes after each checkpoint. Python 3.13,
standard library only, no network, deterministic.

## Approach (ensemble of three, averaged)

For each case, with `last` = the close at the checkpoint:

- **(a) Persistence** — `last`. Bitcoin's 4-hour move is usually small, so the
  checkpoint close is a strong anchor.
- **(b) Slope extrapolation** — least-squares slope of the last 60 closes,
  projected 240 minutes ahead and damped by 0.5, added to `last`.
- **(c) Mean reversion** — `last + 0.10 * (median of the last 1440 closes - last)`.
  Pulls the guess a tenth of the way back toward the 24-hour median.

The final guess is the mean of (a), (b) and (c), clamped to **±1.5% of `last`**
so a noisy short window can never drag the forecast far from the anchor.
Result is rounded to the price grid's 5 decimals and kept inside
(0, 10,000,000).

## Fallback

Fewer than 100 prices, or a non-finite value in the windows used → forecast
is just `last` (persistence), which is always a valid guess.

## Run

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` in the input dir, writes one `<id>.out` per case:
`{"forecasts":[{"case":"<id>","price":<number>}]}`.

## Practice score

House persistence baseline: 44521.576667 cents MAE. See `grade-local` output
in the build report for this entry's practice score.
