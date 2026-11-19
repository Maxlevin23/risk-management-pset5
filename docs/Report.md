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

The Chapter 10 notebook sizes the risk of an 11-position portfolio at **\$616,900 a day**, with a 1-in-255-day loss of **\$1.64 million**. Those figures set hedges and capital, so a Python translation has to be shown to reproduce them, not merely appear to. Across the original portfolio and three new scenarios, it does: **all 36 outputs and all 2,104 displayed cells match Mathematica exactly**, with no cell relying on the one-unit tolerance the assignment allows.

## 1. Test scenarios

A match on one portfolio's rounded output is weak evidence, since a few Table 1 DV01s carry a single significant figure. Each scenario below was built to break a specific pitfall, run through the original Mathematica code, and compared with Python.

| Scenario | What changed | Why (pitfall exercised) |
|---|---|---|
| original | Nothing: the notebook's 11 positions, settle 27-Jan-2009. | Baseline; checked against the notebook PDF. |
| scenario1 (portfolio) | EURCash 0 → 15 and 5yr UST 0 → 40; 10yr UKG 25 → −25; GBPCash moved from Government to Credit. | Zero holdings become real risk; a sign flip reverses contributions and hedges; reassignment changes subportfolio totals. The duplicate "10yr UST" stays in two subportfolios. |
| scenario2 (market data) | Scenario 1 portfolio; GBPFX 1/1.4 → 1/1.6 and USDYld10yr 2.53% → 3.53%, in a modified copy `SamplePort2_scenario2.m`. | FX conversion and the FX risk factor; revaluation and DV01s at a different yield. Original `SamplePort2.m` untouched. |
| scenario3 (stress) | Settle 30-Jun-2009; adds 5yr UKG, 5yr and 10yr Bund, the dated swap `Swap201901`, SPX futures; "10yr UST" held +12.5 and −12.5 in two subportfolios; fractional and zero holdings; new subportfolio names. | Day counts and coupon counting; PV functions the original never calls; duplicates that cancel in total but not per subportfolio; sort order of report rows. |

Each scenario is one Python file in `scenarios/` with the same five names as `src/inputs.py`, paired with one `inputs.m` in `reference/<scenario>/`. The duplicate-security case matters most: keying positions by name would cut reported volatility on the original portfolio from \$616,900 to \$544,900, a 12% understatement of daily risk.

## 2. Verification summary printed by `verify.py`

| Scenario | Outputs | Cells compared | Cells matching | Result |
|---|---|---|---|---|
| original | 9 | 506 | 506 | **PASS**, all nine outputs |
| scenario1 | 9 | 514 | 514 | **PASS**, all nine outputs |
| scenario2 | 9 | 514 | 514 | **PASS**, all nine outputs |
| scenario3 | 9 | 570 | 570 | **PASS**, all nine outputs |

Per output, the original portfolio compares 40 holdings cells, 240 in Table 1, 36 in the category summary, 35 and 21 and 35 in the three contributor and hedge tables, 63 in the replicating portfolios, 24 by subportfolio and 12 in the VaR summary. The original's reference is the notebook PDF, transcribed by hand; scenarios 1 to 3 use full-precision exports from Mathematica 15.0.1 (Wolfram Cloud), which `verify.py` rounds with the notebook's own rules. At full precision, individual functions agree with Mathematica to about one part in 100 billion. Nothing here was checked against Python's own output.

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

Equity and FX together drive 57.6% of the portfolio's risk, even though rates carry the largest stand-alone volatility (\$345,800). All nine tables, for every scenario, appear side by side in `output/verification_report.html`.

## 4. Remaining discrepancies

**None in the displayed tables.** One cell resisted until the end, and it shows why full-precision references matter. FTE Equity carries two DV01s of 6,500,000, which display with one digit; Mathematica shows `7×10^6` for one and `6×10^6` for the other, while Python first showed `7×10^6` for both. The Mathematica export revealed the exact values (6,500,000.000000022 and 6,499,999.999999975) and the cause: Mathematica computes `holding*1000000*x/fx` by multiplying by the reciprocal of the FX rate rather than dividing. Writing `eqtypv` and `eqtyFutpv` in that order now reproduces Mathematica to the last bit.

**Deliberate differences.** Python's holdings table shows all 11 positions where the notebook shows 9, because the notebook hard-codes `n = 9`. With fewer than five risk factors, the notebook's replicating-portfolio loop fails; Python stops at the number available. The Student-t and mixture quantiles use a custom root finder in place of `Quantile` and `FindRoot`, and agree with Mathematica to 15 significant figures. Rerun scenario notebooks and their PDFs sit in `reference/<scenario>/`, and all 538 numbers in the three scenarios' Python tables appear in them in order.

## 5. Testing approach

Three layers of tests, **61 in all, every one passing** (`python tests/run_tests.py` or `pytest`), check the translation from the function up to the finished table.

**Function tests** cover the five groups the assignment names. `tests/test_distfn_vs_mathematica.py` holds 21 tests that compare each translated function with Mathematica's output for the same inputs, to a relative tolerance of one in a billion. The remaining function tests draw on three sources: values Mathematica displays in the notebook (all 18 DV01s, 11 security volatilities, the five VaR rows); closed forms that must hold exactly (a par bond prices at 100 on a coupon date, a swap or CDS at its par rate is worth zero, put-call parity for the bond option); and properties any correct version satisfies (contributions sum to 100%, the best hedge is a true minimum, the mixture quantile inverts its CDF to one part in a trillion across 21 cases).

**Table tests** compare all nine formatted outputs with the notebook, and confirm both that a deliberately wrong reference cell is caught and that the matching rule accepts a one-unit difference but rejects two. **Scenario tests** check pitfall behaviour directly: in scenario 3, offsetting \$12.5 million positions in "10yr UST" leave total volatility unchanged yet remain two rows with opposite DV01s. Because report functions return raw floats and a separate layer rounds them, every test rounds exactly as the notebook does.

**What comes next.** Three steps would keep the translation honest as it changes: run `verify.py` automatically on every commit through a GitHub Actions workflow; store full-precision Mathematica exports, not displayed values, for every future scenario; and add a curve-bootstrapping scenario once `bootstrapcurve` exists, since the `"levelcurveinp"` branch of `populateSecDV01s` is the one branch of the DV01 engine left untranslated. A verified translation today is not a verified translation tomorrow. The choice is between checking proactively on every change and discovering an error after a hedge has already been sized on it.
