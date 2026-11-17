---
title: "Problem 5 Report: Translating the Chapter 10 Risk Reports to Python"
subtitle: "PPHA 42525 Risk Management, Autumn 2026"
geometry: "margin=1.7cm"
fontsize: 9pt
mainfont: "Helvetica Neue"
monofont: "Menlo"
monofontoptions: "Scale=0.8"
pagestyle: empty
---

## 1. Test scenarios

| Scenario | What changed | Why (pitfall exercised) |
|---|---|---|
| original | Nothing: the notebook's 11 positions, settle 27-Jan-2009. | Baseline; checked against the notebook PDF. |
| scenario1 (portfolio) | EURCash 0 → 15 and 5yr UST 0 → 40; 10yr UKG 25 → −25; GBPCash moved from Government to Credit. | Zero holdings become real risk; a sign flip reverses contributions and hedges; reassignment changes subportfolio totals. The duplicate "10yr UST" stays in two subportfolios. |
| scenario2 (market data) | Scenario 1 portfolio; GBPFX 1/1.4 → 1/1.6 and USDYld10yr 2.53% → 3.53%, in a modified copy `SamplePort2_scenario2.m`. | FX conversion and the FX risk factor; revaluation and DV01s at a different yield. Original `SamplePort2.m` untouched. |
| scenario3 (stress) | Settle 30-Jun-2009; adds 5yr UKG, 5yr and 10yr Bund, the dated swap `Swap201901`, SPX futures; "10yr UST" held +12.5 and −12.5 in two subportfolios; fractional and zero holdings; new subportfolio names. | Day counts and coupon counting; PV functions the original never calls; duplicates that cancel in total but not per subportfolio; sort order of report rows. |

Each scenario is one small Python file in `scenarios/` with the same five names as `src/inputs.py`, and one `inputs.m` in `reference/<scenario>/` holding the changed Mathematica lines.

## 2. Verification summary printed by `verify.py`

| Scenario | Outputs | Cells compared | Cells matching | Result |
|---|---|---|---|---|
| original | 9 | 506 | 506 | **PASS**, all nine outputs |
| scenario1 | 9 | 514 | 514 | **PASS**, all nine outputs |
| scenario2 | 9 | 514 | 514 | **PASS**, all nine outputs |
| scenario3 | 9 | 570 | 570 | **PASS**, all nine outputs |

All 36 outputs pass and all 2,104 cells show the identical displayed value; none needed the one-unit tolerance. Per-output cell counts for the original: holdings 40, Table 1 240, category summary 36, top contributors 35, best single hedge 21, best three hedges 35, replicating portfolios 63, subportfolio 24, VaR 12.

The reference for the original portfolio is the displayed values transcribed from the notebook PDF. The references for scenarios 1 to 3 are full-precision numbers exported by `mathematica/RunScenarios.wl`, run in Mathematica 15.0.1 (Wolfram Cloud); `verify.py` rounds them with the notebook's rules before comparing. The same run exported function-level values for the original portfolio (`reference/unit_values.json`): Python agrees with them to a relative difference of about 1e-11 or better (DV01s, variance-covariance matrix, contributions, best hedges, correlations, mixture and Student-t quantiles).

## 3. Sample side-by-side table: risk-category summary (original portfolio)

| | Mathematica Exp Vol (\$) | Python Exp Vol (\$) | Mathematica Contribution | Python Contribution | Mathematica Correlation | Python Correlation |
|---|---|---|---|---|---|---|
| Overall | 616,900 | 616,900 | 100.0 | 100.0 | with portfolio | with portfolio |
| FI - rates | 345,800 | 345,800 | 39.2 | 39.2 | 0.700 | 0.700 |
| FI - swap spreads | 38,760 | 38,760 | -0.4 | -0.4 | -0.071 | -0.071 |
| Credit | 65,190 | 65,190 | 2.8 | 2.8 | 0.265 | 0.265 |
| Equity | 296,400 | 296,400 | 35.8 | 35.8 | 0.746 | 0.746 |
| Commodity | 0 | 0 | 0 | 0 | (blank) | (blank) |
| FX | 236,100 | 236,100 | 21.8 | 21.8 | 0.571 | 0.571 |
| Volatility | 8,678 | 8,678 | 0.7 | 0.7 | 0.510 | 0.510 |

All nine tables appear side by side in `output/verification_report.html`.

## 4. Remaining discrepancies

**None in the displayed tables.** One cell differed in the first complete run and is worth recording. In Table 1 the FTE Equity position has two DV01s that are both 6,500,000 to within 1e-8, yet Mathematica displays them as `7×10^6` (FTEEqSpecific) and `6×10^6` (EURFX), because the display keeps one digit and floating-point noise decides the rounding. Python first showed `7×10^6` for both. The full-precision export showed why: Mathematica evaluates `holding*1000000*x/fx` as (exact integer product) × (x × fx⁻¹), multiplying by a reciprocal instead of dividing. Writing `eqtypv` and `eqtyFutpv` in that order reproduces Mathematica's values to the last bit (6500000.000000022 and 6499999.999999975), and the cell now matches in every scenario.

**Deliberate differences.** (a) Python's holdings table shows all positions; the notebook shows 9 (hard-coded `n = 9`), so the original holdings comparison covers those 9 rows. (b) With fewer than five risk factors the notebook's replicating-portfolio routine fails; Python stops at the number available. (c) The Student-t and mixture quantiles use our own root finder instead of `Quantile`/`FindRoot`; they agree with Mathematica to 15 significant figures.

**Rerun notebooks.** `reference/<scenario>/` holds each rerun notebook (`.nb`) and its PDF, produced from the same Mathematica code; all 538 numeric cells of the three scenarios' Python tables appear in those PDFs in the same order. Differences of order 1e-11 remain at full precision in bump-and-revalue results where operation order differs; they are far below display precision.

## 5. Testing approach

*Three layers, 40 tests, all passing, run with `python tests/run_tests.py` or `pytest`.*

**Function tests** (`tests/test_pv_and_dv01.py`, `tests/test_risk_and_distributions.py`) cover the five groups the assignment lists. Expected values come from three labelled sources: **(M)** values Mathematica displays in the notebook PDF, compared after applying the notebook's rounding (all 18 DV01s, 11 security vols, portfolio vol, replicating assets and percentages, five VaR rows); **(H)** closed forms that must hold exactly (par bond on a coupon date prices at 100; a swap or CDS at its par rate is worth 0; put-call parity for the bond option; cash and FX DV01 equal to USD exposure; accrued interest 73/181 of a coupon; published t-table quantiles); **(P)** properties any correct translation satisfies (contributions sum to 100%; moving a DV01 to its best hedge reproduces `volbesthedge` and any nudge raises volatility; the all-or-nothing figure equals the recomputed change; the mixture quantile inverts the CDF to 1e-12 at seven probabilities and three parameter sets; brute force confirms each stepwise replicating choice).

**Table tests** (`tests/test_tables.py`) compare all nine formatted outputs with `reference/original/tables.json`, confirm that a deliberately wrong reference cell is caught, and confirm the matching rule accepts a one-unit difference but rejects two.

**Scenario tests** run every scenario, check internal consistency, and check pitfall behaviour directly: in scenario 3 the offsetting "10yr UST" positions leave total volatility unchanged yet remain two rows with opposite DV01s. Two further tests compare every scenario table and the function-level values with the Mathematica exports; they report SKIPPED, not passed, if those files are missing.

Raw numbers and display are separate (`reports.py` returns floats, `formatting.py` rounds), so tests round exactly as the notebook does. The reference values were transcribed from the assignment PDF, not copied from Python output.
