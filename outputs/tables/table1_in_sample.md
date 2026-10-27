# Table 1 · Commodity returns and FX returns, in sample

| sample | h | β (SE) | 95% CI | 1-SD effect, % | p | Holm p | partial R², % | MDE partial R², % | N | dates | spec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CAD | 0 | +0.0613 (0.0052) | [+0.0512, +0.0715] | +0.154 | <0.001 | <0.001 | 14.46 | 0.94 | 3766 | 2010-01-05 → 2025-09-19 | CAD.baseline.h0.ols |
| CAD | 1 | -0.0020 (0.0045) | [-0.0107, +0.0068] | -0.005 | 0.661 | 1.000 | 0.01 | 0.43 | 3765 | 2010-01-05 → 2025-09-18 | CAD.baseline.h1.ols |
| CAD | 5 | -0.0043 (0.0032) | [-0.0106, +0.0020] | -0.011 | 0.183 |  | 0.05 | 0.22 | 3761 | 2010-01-05 → 2025-09-12 | CAD.baseline.h5.ols |
| CLP | 0 | +0.1800 (0.0101) | [+0.1602, +0.1999] | +0.240 | <0.001 | <0.001 | 10.01 | 0.27 | 3629 | 2010-01-05 → 2025-09-23 | CLP.baseline.h0.ols |
| CLP | 1 | +0.0186 (0.0115) | [-0.0040, +0.0412] | +0.025 | 0.106 | 0.318 | 0.10 | 0.29 | 3612 | 2010-01-05 → 2025-09-23 | CLP.baseline.h1.ols |
| CLP | 5 | +0.0040 (0.0107) | [-0.0169, +0.0250] | +0.005 | 0.706 |  | 0.00 | 0.25 | 3613 | 2010-01-05 → 2025-09-23 | CLP.baseline.h5.ols |
| NOK | 0 | +0.0984 (0.0100) | [+0.0788, +0.1179] | +0.217 | <0.001 | <0.001 | 16.19 | 1.54 | 3774 | 2010-01-05 → 2025-09-23 | NOK.baseline.h0.ols |
| NOK | 1 | +0.0045 (0.0074) | [-0.0099, +0.0190] | +0.010 | 0.539 | 1.000 | 0.02 | 0.37 | 3774 | 2010-01-05 → 2025-09-23 | NOK.baseline.h1.ols |
| NOK | 5 | +0.0013 (0.0061) | [-0.0107, +0.0133] | +0.003 | 0.831 |  | 0.00 | 0.25 | 3774 | 2010-01-05 → 2025-09-23 | NOK.baseline.h5.ols |
| POOLED | 0 | +0.0889 (0.0060) | [+0.0772, +0.1006] | +0.185 | <0.001 |  | 9.92 | 0.39 | 11169 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h0.ols |
| POOLED | 0 | +0.0889 (0.0214) | [-0.0030, +0.1808] | +0.185 | 0.053 |  | 9.92 | 15.46 | 11169 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h0.ols_two_way_cluster |
| POOLED | 1 | +0.0033 (0.0045) | [-0.0056, +0.0121] | +0.007 | 0.468 |  | 0.01 | 0.15 | 11151 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h1.ols |
| POOLED | 1 | +0.0033 (0.0048) | [-0.0172, +0.0237] | +0.007 | 0.563 |  | 0.01 | 0.61 | 11151 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h1.ols_two_way_cluster |
| POOLED | 5 | -0.0011 (0.0038) | [-0.0085, +0.0062] | -0.002 | 0.761 |  | 0.00 | 0.10 | 11148 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h5.ols |
| POOLED | 5 | -0.0011 (0.0041) | [-0.0189, +0.0166] | -0.002 | 0.808 |  | 0.00 | 0.46 | 11148 | 2010-01-05 → 2025-09-23 | POOLED.baseline.h5.ols_two_way_cluster |

**Reading.**
- **CAD, same day.** A one-SD daily WTI move (2.51%) goes with a +0.154% CAD move (95% CI +0.128 to +0.180).
- **CAD, next day.** We could have detected a partial R² of 0.43% at 80% power; we found 0.01% (β -0.0020, MDE β 0.0125).
- **CLP, same day.** A one-SD daily LME copper move (1.33%) goes with a +0.240% CLP move (95% CI +0.214 to +0.267).
- **CLP, next day.** We could have detected a partial R² of 0.29% at 80% power; we found 0.10% (β +0.0186, MDE β 0.0322).
- **NOK, same day.** A one-SD daily Brent move (2.21%) goes with a +0.217% NOK move (95% CI +0.174 to +0.260).
- **NOK, next day.** We could have detected a partial R² of 0.37% at 80% power; we found 0.02% (β +0.0045, MDE β 0.0207).

**Note.** Daily log returns, sign convention A (positive = the commodity currency appreciates against USD). Δs_{t+h} = α + β·Δc_t + γ·ΔDXY_t + δ·ΔBCOM⊥_t; h = 5 is the one-day return five trading days ahead. Per pair: Newey–West HAC, normal reference. Pooled (CAD, CLP, NOK; AUD excluded by D7): pair fixed effects, Driscoll–Kraay errors with a normal reference (D1 as amended 2026-10-26). The frozen two-way estimator is reported on the second row of each horizon — same coefficient, different standard error. Two-way clustering needs the cluster count to grow in both dimensions and G_pair = 3; a synthetic Monte Carlo put its size at 0.5% against a nominal 5% (Driscoll–Kraay 4.5%), so it is invalid here rather than merely conservative. The amendment changes no coefficient and leaves both predictive nulls null. 1-SD effect: β × SD(Δc) of the estimation sample, in percent. Holm across the six primary tests ({CAD, CLP, NOK} × {h = 0, 1}). MDE: two-sided 5%, 80% power, as partial R² of Δc. Rules fixed in design_decisions.md, Amendments, 2026-10-26.
