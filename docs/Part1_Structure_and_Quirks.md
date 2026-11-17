---
title: "Problem 5, Part I: Structure of the Chapter 10 Code"
subtitle: "PPHA 42525 Risk Management, Autumn 2026 (checkpoint deliverable)"
geometry: "margin=1.6cm"
fontsize: 9pt
mainfont: "Helvetica Neue"
monofont: "Menlo"
monofontoptions: "Scale=0.82"
pagestyle: empty
---

**How the three files fit together.** `SamplePort2.m` is data only: parallel lists indexed by position (security `i` owns entry `i` of `secParmValues`, `secMktInputNames`, `secRiskFactorNames`, `secPVFunction`). `DistFn1.m` is the engine: PV functions, bump-and-revalue DV01s, the variance-covariance matrix, and risk measures; its functions read the `SamplePort2.m` lists as globals. `Tables_Ch10.nb` is a script: it sets `seclist`, `holdings`, `subportfolio`, defines the table functions, and calls them. Every risk number flows through one chain: **PV functions → `populateSecDV01s` → `populatePortDV01s` → `populateVCV` → `portVolbyVCVextended`**.

## 1. Dependency map (output → functions → inputs)

| # | Output (notebook call) | `DistFn1.m` functions that produce it | `SamplePort2.m` lists that feed them |
|-|------|-------------|-------------|
| 1 | Holdings, `Out[38]` | `fxrateSec` | `secNames`, `secParmNames`, `secParmValues` (Currency), `marketDataNames/Values` |
| 2 | Table 1, `displayRF` | `populateSecDV01s` → `pvposn` → PV functions (`bondpv`/`bondprc`/`pv`, `swappv`, `bondoptionpv`, `simpCDSpv`, `eqtypv`, `eqtyFutpv`, `cashpv`); `secVolbyVCV`, `populateVCV`, `fxsymb` | all `sec*` lists; `riskFactorNames`, `BumpSize`, `BumpTypes`, `BumpUnit`; `marketDataNames/Values`, `marketVols`, `corrmatrix`; `settledate` |
| 3 | Category summary, `reportFunction1[[1]]` | `portVolbyVCVextended` → `populatePortDV01s`, `populateEqvDV01s`, `populateVCV` | as #2 plus `riskFactorCategory`, `riskFactorEqvs` |
| 4-6 | Contributors and hedges, `reportFunction1[[2..4]]` via `tableContributers` | `portVolbyVCVextended` items 3-7, 11; `populateEqvDV01s` converts DV01s to "mn of equivalent security" | as #3; `riskFactorEqvs` matters most |
| 7 | Replicating portfolios, `reportFunction1[[5]]` via `bestReplicatePort` | `portVolbyVCVextended` items 8, 9, 12, 13; `LinearSolve` | as #3 |
| 8 | By subportfolio, `volbySubPortfolio` | `portVolbyVCVextended`, once for the whole portfolio and once per subportfolio with other holdings zeroed | as #3 plus the notebook's `subportfolio` |
| 9 | VaR, `varsumm` | `portVolbyVCV`; built-in `Quantile`, `StudentTDistribution`, `MixtureDistribution` | as #3 |

## 2. Quirks and traps

1. **Why the holdings display shows 9 of 11.** The display cell hard-codes `n = 9` and builds `Table[..., {i, n}]`, so EURCash and 5yr UST (the two zero holdings) are never drawn. The same cell loops `For[i = 1, i < Length[seclist], ...]` (strict `<`), so position 11 never gets its currency symbol either. Python shows all 11.
2. **Duplicate security.** "10yr UST" is position 1 (Government, 20) and position 3 (Swaps, 30). Mathematica works by list position, so they stay apart; a dict or a pandas index keyed on name would merge or overwrite them. Python keeps a 1-based `Position` id.
3. **Zero holdings still matter.** EURCash and 5yr UST have DV01 0 but still add EURFX and USDYld5yr to the risk-factor list. `volbySubPortfolio` relies on this: it zeroes holdings rather than dropping positions, so each subportfolio's DV01 vector lines up with the full one.
4. **Empty category.** Commodity has no risk factors: volatility 0, contribution integer `0` (shown "0", not "0.0"), and correlation blank because the code tests `zz > 0` before dividing.
5. **FX direction.** FX is quoted as foreign currency per USD (GBPFX = 1/1.4) and PVs are *divided* by it. FX DV01s are per 100% *fall* in the rate (`riskFactorBumpUnit = -1`), yield DV01s per 1bp *fall*; `populateVCV` multiplies each correlation by the two bump-unit signs to compensate.
6. **`eqtyFutpv` ignores bumped FX.** It reads the global `marketDataValues`, not its `inputs`, so futures never show FX risk. Kept deliberately.
7. **Two different mixture settings.** `DistFn1.m` sets `alpha = 0.05, beta = 3` and defines its own `pdf/cdf/quantile`; `varsumm` overrides with `alpha = 0.01, beta = 5` and uses the built-in `MixtureDistribution`. A translator who trusts `DistFn1.m` gets the wrong VaR.
8. **Dates.** `bondprc` puts the settlement *year* into the maturity date to find the surrounding coupon dates, uses actual days for the fractional period, and `Round`s (half to even) the remaining coupon count from days/(365/freq). A bond is told from a swap by `Length[parms] == 5`.
9. **Stepwise selection.** `bestReplicatePort` is greedy with strict `<`, so the first asset wins ties; `Ordering` is stable. With fewer than five risk factors the Mathematica loop reuses a stale index and `LinearSolve` fails; Python stops early.
10. **Display rounding.** `NumberForm[x, {5, 0}]` switches to scientific at 10^6 with a one-digit mantissa ("4×10^7"), so those cells carry one significant figure and say little about correctness. Agreement on one portfolio is weak evidence, hence the new scenarios.
11. **Matrix orientation and indexing.** Lists are 1-based; `corrmatrix` is ordered by `marketDataNames` (18 items), not `riskFactorNames` (17 items, different order), so every look-up needs both indexes. `intermedvec = d * cov` is element-wise, not a dot product.
