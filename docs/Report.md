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
| original | 9 | 506 | 506 (505 identical, 1 within one unit) | **PASS**, all nine outputs |
| scenario1 | 9 | – | – | **NO REFERENCE** (Mathematica run pending) |
| scenario2 | 9 | – | – | **NO REFERENCE** (Mathematica run pending) |
| scenario3 | 9 | – | – | **NO REFERENCE** (Mathematica run pending) |

Per-output cell counts for the original: holdings 40/40, Table 1 240/240, category summary 36/36, top contributors 35/35, best single hedge 21/21, best three hedges 35/35, replicating portfolios 63/63, subportfolio 24/24, VaR 12/12.

**The scenarios have not yet been compared with Mathematica.** The Python side runs for all three and the Mathematica inputs and export script (`mathematica/RunScenarios.wl`) are in the repository, but no Mathematica kernel was available when this was written. After that script is run, `python verify.py` fills in the three rows above; this section must be updated with the result before submission.

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

**One cell, within the allowed tolerance.** Table 1, FTE Equity, EURFX DV01: Mathematica displays `6×10^6`, Python `7×10^6`. The DV01 is exactly 6,500,000 (EUR 5mn at 1.30) and the display keeps a single digit, so the result depends on floating-point noise of about 1e-8 in the bump-and-revalue arithmetic; Python computes 6,500,000.00000002. The FTEEqSpecific DV01 on the same position, also 6,500,000, displays `7×10^6` in both. Its downstream value (RF position vol 51,410) matches exactly. No attempt was made to imitate Mathematica's operation order to force the digit.

**Deliberate differences.** (a) Python's holdings table shows all 11 positions; the notebook shows 9 (hard-coded `n = 9`). (b) With fewer than five risk factors the notebook's replicating-portfolio routine fails; Python stops at the number available. (c) The Student-t and mixture quantiles use our own root finder instead of `Quantile`/`FindRoot`; agreement is to 1e-12 on the CDF, far inside display precision.

**Not yet established.** Agreement on scenarios 1 to 3 (see section 2), and full-precision agreement of individual functions (`reference/unit_values.json` is produced by the same Mathematica script).

## 5. Testing approach

*Three layers, 40 tests, run with `python tests/run_tests.py` or `pytest`.*

**Function tests** (`tests/test_pv_and_dv01.py`, `tests/test_risk_and_distributions.py`) cover the five groups the assignment lists. Because Mathematica could not be called, expected values come from three labelled sources: **(M)** values Mathematica displays in the notebook PDF, compared after applying the notebook's rounding (all 18 DV01s, 11 security vols, portfolio vol, replicating assets and percentages, five VaR rows); **(H)** closed forms that must hold exactly (par bond on a coupon date prices at 100; a swap or CDS at its par rate is worth 0; put-call parity for the bond option; cash and FX DV01 equal to USD exposure; accrued interest 73/181 of a coupon; published t-table quantiles); **(P)** properties any correct translation satisfies (contributions sum to 100%; moving a DV01 to its best hedge reproduces `volbesthedge` and any nudge raises volatility; the all-or-nothing figure equals the recomputed change; the mixture quantile inverts the CDF to 1e-12 at seven probabilities and three parameter sets; brute force confirms each stepwise replicating choice).

**Table tests** (`tests/test_tables.py`) compare all nine formatted outputs with `reference/original/tables.json`, confirm that a deliberately wrong reference cell is caught, and confirm the matching rule accepts a one-unit difference but rejects two.

**Scenario tests** run every scenario, check internal consistency, and check pitfall behaviour directly: in scenario 3 the offsetting "10yr UST" positions leave total volatility unchanged yet remain two rows with opposite DV01s. Two tests compare against Mathematica exports and report SKIPPED until those files exist, rather than passing silently.

Raw numbers and display are separate (`reports.py` returns floats, `formatting.py` rounds), so tests round exactly as the notebook does. The reference values were transcribed from the assignment PDF, not copied from Python output.
