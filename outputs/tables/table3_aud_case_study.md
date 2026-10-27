# Table 3 · AUD and iron ore: what the instrument does

| treatment | h | β (SE) | 95% CI | 1-SD effect, % | p | partial R², % | CW p (OOS) | MDE partial R², % | N | dates | spec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| first8 | 0 | +0.0166 (0.0080) | [+0.0010, +0.0322] | +0.030 | 0.037 | 0.32 |  | 0.57 | 1023 | 2013-04-09 → 2025-09-10 | AUD.first8.h0.ols |
| first8 | 1 | +0.0025 (0.0109) | [-0.0189, +0.0239] | +0.004 | 0.819 | 0.00 | 0.565 | 0.60 | 1023 | 2013-04-09 → 2025-09-10 | AUD.first8.h1.ols |
| first8 | 5 | +0.0007 (0.0122) | [-0.0232, +0.0247] | +0.001 | 0.952 | 0.00 | 0.678 | 0.79 | 1023 | 2013-04-09 → 2025-09-10 | AUD.first8.h5.ols |
| first5 | 0 | +0.0125 (0.0106) | [-0.0082, +0.0332] | +0.023 | 0.235 | 0.17 |  | 0.95 | 575 | 2013-04-09 → 2025-09-05 | AUD.first5.h0.ols |
| first5 | 1 | +0.0123 (0.0134) | [-0.0139, +0.0385] | +0.023 | 0.356 | 0.11 | 0.211 | 0.99 | 575 | 2013-04-09 → 2025-09-05 | AUD.first5.h1.ols |
| first5 | 5 | +0.0014 (0.0147) | [-0.0274, +0.0302] | +0.003 | 0.923 | 0.00 | 0.668 | 1.20 | 575 | 2013-04-09 → 2025-09-05 | AUD.first5.h5.ols |
| full | 0 | +0.0166 (0.0069) | [+0.0031, +0.0301] | +0.021 | 0.016 | 0.19 |  | 0.25 | 2963 | 2013-04-09 → 2025-09-19 | AUD.full.h0.ols |
| full | 1 | +0.0039 (0.0087) | [-0.0131, +0.0210] | +0.005 | 0.651 | 0.01 | 0.403 | 0.24 | 2962 | 2013-04-09 → 2025-09-18 | AUD.full.h1.ols |
| full | 5 | -0.0069 (0.0099) | [-0.0264, +0.0126] | -0.009 | 0.489 | 0.02 | 0.194 | 0.30 | 2958 | 2013-04-09 → 2025-09-12 | AUD.full.h5.ols |
| rescaled | 0 | +0.0075 (0.0038) | [+0.0001, +0.0149] | +0.018 | 0.047 | 0.14 |  | 0.27 | 2963 | 2013-04-09 → 2025-09-19 | AUD.rescaled.h0.ols |
| rescaled | 1 | +0.0007 (0.0047) | [-0.0086, +0.0100] | +0.002 | 0.883 | 0.00 | 0.427 | 0.26 | 2962 | 2013-04-09 → 2025-09-18 | AUD.rescaled.h1.ols |
| rescaled | 5 | -0.0075 (0.0051) | [-0.0174, +0.0025] | -0.018 | 0.141 | 0.08 | 0.155 | 0.29 | 2958 | 2013-04-09 → 2025-09-12 | AUD.rescaled.h5.ols |

**Note.** A methodological case study, never a fourth comparison point (D7). `SCO1` settles on the monthly average of IODEX prints, so pass-through falls as w = (N−k+1)/N through the contract month. **first8** is the DD-12 baseline (k ≤ 8, w 1.00 → 0.68); **first5** k ≤ 5; **full** every day; **rescaled** the full sample with Δc / w. The point is the pattern across treatments, not any one number; the coefficient evidence is weak (D7). Timing (D5): iron ore settles 10.5 h before the FX snap (range 10.5–11.5 h, 37.8% of days off-mode; settlement times unverified), so the same-day FX return contains most of a trading day after the commodity print. Not Holm-adjusted. Other columns as Table 1.
