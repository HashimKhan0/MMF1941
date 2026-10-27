# Table 2 · Out-of-sample loss relative to the random walk

| sample | h | test period | P | OOS R², % | CW gain, % of RW MSPE [95% CI] | CW stat | p (one-sided) | MDE, % of RW MSPE | MAE ratio | spec |
|---|---|---|---|---|---|---|---|---|---|---|
| CAD | 1 | 2017-11-06 → 2025-09-18 | 1883 | -0.39 | -0.01 [-0.73, +0.71] | -0.04 | 0.514 | 0.91 | 1.003 | CAD.baseline.h1.cw |
| CAD | 5 | 2017-11-02 → 2025-09-12 | 1881 | -0.00 | +0.24 [-0.22, +0.70] | +1.01 | 0.157 | 0.59 | 1.000 | CAD.baseline.h5.cw |
| CLP | 1 | 2018-03-23 → 2025-09-23 | 1806 | +0.00 | +0.41 [-0.19, +1.02] | +1.33 | 0.091 | 0.77 | 1.000 | CLP.baseline.h1.cw |
| CLP | 5 | 2018-03-22 → 2025-09-23 | 1807 | -0.18 | -0.04 [-0.40, +0.32] | -0.20 | 0.579 | 0.46 | 1.001 | CLP.baseline.h5.cw |
| NOK | 1 | 2017-11-14 → 2025-09-23 | 1887 | -0.28 | -0.15 [-0.65, +0.35] | -0.58 | 0.719 | 0.63 | 1.003 | NOK.baseline.h1.cw |
| NOK | 5 | 2017-11-14 → 2025-09-23 | 1887 | -0.15 | +0.10 [-0.55, +0.76] | +0.31 | 0.377 | 0.83 | 1.000 | NOK.baseline.h5.cw |

**Note.** Expanding window; the model is refitted at every origin on rows whose target date is on or before the origin; forecasts start at the sample midpoint. Benchmark: driftless random walk (zero return forecast). Clark–West (2007), not Diebold–Mariano: the model nests the benchmark (DD-11; deviates from the brief, flagged for the supervisor). Squared-error loss; OOS R² and the MAE ratio (model/RW, below 1 favours the model) are descriptive. MDE: one-sided 5%, 80% power. Per-origin forecasts: outputs/models/oos_forecasts.csv.
