# Detailed implementation guide: Commodity-Currency Transmission Beyond a Single Pair: A Multi-Pair Replication

- Student: Khan, Hashim
- Assignment: Project 1
- Proposal ID: A14-03
- Official area: A14 — FX & currencies
- Companion brief: `project_1.md`
- Data not ready: 100.0%
- Estimated data not available locally: 50.0%

## Purpose and scope

This guide turns the approved project brief into an auditable implementation sequence. It preserves the research question, hypothesis and model family in the companion brief. Choices listed under **Decisions to confirm before estimation** must be settled with the supervisor and recorded before the primary results are examined.

## Approved research target

### Main question

Does the contemporaneous-strong / predictively-weak commodity->currency pattern (soybean->BRL, project 12) generalize to AUD-iron ore, CAD-WTI, CLP-copper, NOK-Brent at daily frequency, net of broad-dollar (DXY) and broad-commodity (BCOM)?

### Testable hypothesis

Each pair shows a significant contemporaneous commodity->FX transmission that survives DXY+BCOM controls, while the predictive (lagged) direction is a null.

### Operational summary

- Observational unit: currency-day.
- Primary outcome: spot FX return.
- Main signal, treatment or exposure: matched commodity return.
- Benchmark or comparison: random walk plus DXY and broad-commodity controls.
- Primary estimand: pair-specific and pooled predictive commodity-to-currency slope.
- Proposed sample: ~2010-2025 daily.
- Primary assets: AUD, CAD, CLP, NOK vs USD + matched commodity indices.

## Decisions to confirm before estimation

- FX quote convention and close times.
- Commodity mapping and predictive horizon.

Do not choose among these alternatives by comparing final significance or performance. Record the decision, rationale, date and approving supervisor in `design_decisions.md`.

## Required data

### Full requirement from the project inventory

1. daily FX spot (AUD,CAD,CLP,NOK) -> 02_market/fx [not local BBG/Datastream]
2. commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### Bloomberg acquisition assigned to the student

Daily AUD, CAD, CLP and NOK spot rates; iron ore, WTI, copper and Brent prices; BCOM and DXY.

All Bloomberg retrieval must be end-of-day, daily, weekly, monthly, quarterly, annual, event/reference or document data. Any required minute-level or intraday series must come only from `C:\risklab\data\intraday_data`.

### Local data already identified

1. Mixed local/external: daily FX spot (AUD,CAD,CLP,NOK) -> 02_market/fx [not local BBG/Datastream]
2. Mixed local/external: commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### Local data requiring preparation

1. commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

### Data not currently available locally

1. Mixed local/external: daily FX spot (AUD,CAD,CLP,NOK) -> 02_market/fx [not local BBG/Datastream]
2. Mixed local/external: commodity prices (iron ore, WTI, copper, Brent) + BCOM, DXY -> 04_macro/commodities, 02_market [partial coverage or preparation/not local]

## Bloomberg retrieval procedure

Use `FLDS <GO>` to confirm field mnemonics and definitions, `BDP` for static references, `BDH` for end-of-day histories, and `BDS` or the relevant terminal event screen for bulk constituents or event records.

The field names below are candidates and routing aids, not a substitute for terminal verification. Confirm every mnemonic and definition with `FLDS <GO>` for the actual security type and entitlement.

| Requirement | Candidate fields or route | Mandatory validation |
|---|---|---|
| Stable identifiers | ID_BB_GLOBAL, ID_ISIN, TICKER_AND_EXCH_CODE | Confirm identifier history and exchange mapping. |
| Currency and classification | CRNCY plus the relevant sector, country or asset classification | Check changes through time and do not infer missing classifications from current values. |
| FX prices | PX_LAST, forward points and policy/risk-free-rate series | Fix quote direction, tenor and scaling. |
| Macro and commodity controls | CPI, reserves, terms of trade, DXY and commodity benchmarks | Lag releases to public availability and align closes. |

### Pilot before the full pull

1. Test two representative securities or series over ten dates.
2. Confirm that timestamps, currencies, units and adjustments match the intended construct.
3. Compare at least three observations with the terminal display or source document.
4. Test one known corporate action, event date, roll date or release revision where relevant.
5. Save the pilot, field definitions and validation notes before scaling the retrieval.
6. Use one raw file per coherent table and never paste values manually into the analysis panel.

Create `bloomberg_source_log.csv` with these columns:

`source_type, provider, terminal_function, security_or_series_id, field, field_description, frequency, start, end, currency, units, timezone, adjustment, retrieval_date, file_name, file_hash, notes`

## RiskLab data-catalog procedure

1. Search `C:\risklab\data\_catalog\catalog.csv` for non-intraday datasets by construct, fields, asset class and date coverage.
2. Search `C:\risklab\data\bloomberg\inventory.csv` for Bloomberg holdings already present.
3. Search other provider inventories for possible alternatives, but do not treat a similar filename as construct equivalence.
4. Search `C:\risklab\data\_catalog\intraday_inventory.csv.gz` only when the approved design requires minute-level or option-chain data.
5. Resolve current paths through `C:\risklab\data\_catalog\data_paths.py`; retain stable dataset IDs in the manifest.
6. Classify each requirement as `AVAILABLE`, `PARTIAL`, `METADATA REVIEW` or `MISSING`.
7. Verify point-in-time status, adjustment, units, currency, timezone, universe, licence and survivorship before scientific use.

Create `data_manifest.csv` with these columns:

`dataset_id, source_path, provider, construct, role, unit, frequency, start, end, join_keys, point_in_time_status, adjustment, currency, timezone, license, validation_status, exclusions, notes`

## Recommended project structure

```text
project_1/
  README.md
  design_decisions.md
  config/
    project_config.yaml
  manifests/
    data_manifest.csv
    bloomberg_source_log.csv
    sample_attrition.csv
  data/
    raw_bloomberg/
    interim/
    analytic/
  src/
    00_design_freeze
    01_source_inventory
    02_raw_validation
    03_build_events_or_signals
    04_build_outcomes
    05_merge_analysis_panel
    06_descriptive_diagnostics
    07_primary_estimation
    08_robustness
    09_tables_figures
  outputs/
    tables/
    figures/
    diagnostics/
    models/
  paper/
```

Keep provider data immutable. Derived files belong in `interim` or `analytic`, never beside source files.

## End-to-end implementation sequence

1. Read the original brief and copy unresolved decisions into `design_decisions.md`.
2. Freeze the research unit, outcome, signal/treatment, benchmark, estimand, sample, event windows and exclusions before the primary run.
3. Translate every required construct into one row of `data_manifest.csv`.
4. Resolve local sources through the RiskLab catalog; never edit the provider files.
5. Run a small Bloomberg pilot, validate fields and dates, then retrieve only approved non-intraday data.
6. Freeze raw files and hashes; perform schema and economic-validity checks before merging.
7. Build signals/events and outcomes in separate steps, then join with an explicit match report.
8. Produce descriptive coverage and pre-estimation diagnostics; stop if key timing or universe assumptions fail.
9. Run the baseline model and save estimates, standard errors, sample counts and configuration together.
10. Run only prespecified robustness checks, placebos and out-of-sample comparisons.
11. Reconcile all numbers used in the paper to one machine-readable results table.
12. Archive the source log, manifest, design decisions, code, environment record and final outputs together.

## Project-specific construction and estimation hints

1. Fix the FX quote direction so positive returns have the same economic interpretation across pairs.
2. Match each currency to a predeclared commodity benchmark.
3. Align commodity and FX closes to prevent same-day timing leakage.
4. Estimate contemporaneous association separately from true next-period prediction.
5. Define a forecast-origin table and the information available at each origin.
6. Fit preprocessing and models only inside the expanding training window.
7. Issue benchmark and candidate forecasts for identical dates.
8. Evaluate each horizon with a predeclared loss function.
9. Use Diebold-Mariano or Clark-West only where its nesting assumptions fit.
10. Fix FX quote directions and forward-point scaling.
11. Align global market closes and daylight-saving transitions.
12. Include realistic carry, financing and stress-period transaction costs.

## Baseline statistical specification

The companion brief specifies the primary method as:

> Per-pair HAC-OLS with DXY/BCOM controls; pooled panel with pair FE; predictive OOS (Diebold-Mariano) for the null direction.

Use that method as the baseline. The following notation is an implementation aid and must be adapted without changing the approved estimand:

- $y_{t+h}=\alpha+\beta x_t+\gamma'z_t+\varepsilon_{t+h}$
- $e^{model}_{t+h}=y_{t+h}-\widehat{y}^{model}_{t+h|t}$
- $\Delta L_t=L(e^{benchmark}_t)-L(e^{model}_t)$

At minimum, save the coefficient or portfolio effect, standard error, confidence interval, p-value where appropriate, economic units, observations, entities/events, sample dates and specification identifier. Report effect sizes in economically interpretable units in addition to statistical significance.

## Secondary robustness specification

The companion brief proposes:

> Walk-forward RF for the predictive direction vs random walk; DSR. Robustness.

Treat this as robustness, not as a replacement for the primary model. Fit every transformation, feature selection step and tuning choice inside the training sample. Use chronological splits, purging and embargo where labels or holding periods overlap. Compare against the same simple benchmark on identical test observations. Preserve failed folds and infeasible models in the diagnostics.

## Validation and falsification checks

1. Non-synchronous closes can manufacture lead-lag effects.
2. Commodity exposure changes across countries and time.
3. USD-wide moves can dominate bilateral relationships.
4. Training and test coverage by horizon.
5. Forecast errors through time and by regime.
6. Calibration, bias and residual autocorrelation.
7. Performance sensitivity to the fixed test start and benchmark.

Also run these universal checks:

- Duplicate-key and many-to-many join audit.
- Date-shift test that moves signals or events one period backward and forward.
- Negative-control or placebo outcome where economically defensible.
- Influence check excluding the largest event, issuer, asset or crisis period one at a time.
- Common-sample comparison for every model horse-race.
- Results with and without the most consequential data-quality exclusions.
- Sign-convention test using a hand-calculated example.
- Reproduction of five randomly selected observations from raw source to final variable.

## Output plan

### Tables

1. **Table 1: Forecast information set and transformations.** Include observations, dates, units, estimate, uncertainty and the exact specification label.
2. **Table 2: Out-of-sample loss relative to benchmarks.** Include observations, dates, units, estimate, uncertainty and the exact specification label.
3. **Table 3: Stability, calibration and robustness.** Include observations, dates, units, estimate, uncertainty and the exact specification label.

4. **Table 4: robustness and falsification summary.** Include every prespecified robustness result, including failures and nulls.
5. **Appendix table: data lineage and attrition.** Show source coverage, filters, unmatched records and final counts.

### Figures

1. **Figure 1: Actual versus forecast through the test period.** Show sample coverage and uncertainty; label event time, horizon or portfolio definition explicitly.
2. **Figure 2: Cumulative loss differential.** Show sample coverage and uncertainty; label event time, horizon or portfolio definition explicitly.
3. **Figure 3: Rolling or regime-specific forecast performance.** Show sample coverage and uncertainty; label event time, horizon or portfolio definition explicitly.

4. **Figure 4: implementation or data-quality diagnostic.** Use the most important risk identified above.

Every table and figure should display the sample period, frequency, units and a concise note defining the construction.

## Suggested code-module responsibilities

- `00_design_freeze` — stores the approved estimand, windows, universe, exclusions and sign conventions.
- `01_source_inventory` — resolves local catalog records and checks source coverage.
- `02_raw_validation` — validates schemas, identifiers, timestamps, duplicates, units and missingness.
- `03_build_events_or_signals` — creates event, signal or treatment tables without outcome information.
- `04_build_outcomes` — constructs returns, spreads, forecasts or payoffs independently.
- `05_merge_analysis_panel` — performs audited joins and emits an attrition table.
- `06_descriptive_diagnostics` — produces coverage, distributions and pre-estimation plots.
- `07_primary_estimation` — runs only the frozen baseline specifications.
- `08_robustness` — runs the prespecified alternatives and placebos.
- `09_tables_figures` — creates publication-ready outputs directly from saved results.

Each module should read declared inputs, write declared outputs and emit a short validation summary. Configuration values belong in one configuration file rather than being repeated throughout scripts or notebooks.

## Common failure modes and responses

- Non-synchronous closes can manufacture lead-lag effects. Response: quantify its incidence, preserve an explicit flag, and report a sensitivity analysis rather than silently deleting observations.
- Commodity exposure changes across countries and time. Response: quantify its incidence, preserve an explicit flag, and report a sensitivity analysis rather than silently deleting observations.
- USD-wide moves can dominate bilateral relationships. Response: quantify its incidence, preserve an explicit flag, and report a sensitivity analysis rather than silently deleting observations.
- If Bloomberg coverage is thinner than expected, produce a coverage matrix before narrowing the universe or dates; any consequential scope change requires supervisor approval.
- If local and Bloomberg values disagree, compare timestamps, currency, adjustment, units and identifier history before selecting a source.
- If the main result changes sign under a reasonable convention, present the boundary clearly and do not choose the convention based on significance.
- If an estimator fails on some dates, retain the failure rate and determine whether failures are economically selected.

## Minimum reproducibility record

- Research question and frozen estimand.
- Design-decision log with approval dates.
- Bloomberg source log and local-data manifest.
- Raw-file hashes and retrieval dates.
- Environment and package versions.
- Variable dictionary with formulas, units and timing.
- Sample-flow and exclusion table.
- Seed values for resampling and fitted procedures.
- Saved primary and robustness result tables.
- Script that rebuilds every final table and figure.

## Completion checklist

- [ ] Every raw input is listed with a stable identifier, path or source record and hash.
- [ ] Every variable has a definition, unit, timestamp and availability lag.
- [ ] All joins report unmatched and duplicate keys.
- [ ] The final sample can be recreated from raw inputs in one documented sequence.
- [ ] The main estimate uses the frozen sample and specification.
- [ ] Standard errors match the dependence structure.
- [ ] Economic magnitudes, costs and confidence intervals are reported together.
- [ ] Null and adverse results remain in the output.
- [ ] All tables and figures are rebuilt from saved results rather than edited manually.
- [ ] No Bloomberg high-frequency series is requested or downloaded.

## First supervisor checkpoint

Bring the following before the full analysis: the completed design-decision log, data manifest, Bloomberg pilot and field definitions, sample-coverage table, ten hand-checked observations, one preliminary descriptive figure and a written list of unresolved data limitations. Do not present a primary hypothesis test until these items are reviewed.
