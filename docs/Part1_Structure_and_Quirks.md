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

Risk reports are only as trustworthy as the code behind them. The Chapter 10 notebook turns an 11-position, three-currency portfolio into one number a desk acts on: a daily volatility of **\$616,900** and a 1-in-255-day loss of **\$1.64 million**. Small translation errors move those numbers a long way, and the costs are real: hedges sized wrong, capital held against risk that is not there, or risk left unhedged. This page maps how the code produces each report and lists the traps that would break a Python version.

**How the three files fit together.** `SamplePort2.m` is pure data: parallel lists linked by position, so security *i* owns entry *i* of `secParmValues`, `secMktInputNames`, `secRiskFactorNames` and `secPVFunction`. `DistFn1.m` is the engine: PV functions, bump-and-revalue DV01s, the variance-covariance matrix and the risk measures, all reading those lists as globals. `Tables_Ch10.nb` is a script that sets `seclist`, `holdings` and `subportfolio`, defines the table functions, and calls them. Every risk number passes through one chain: **PV functions → `populateSecDV01s` → `populatePortDV01s` → `populateVCV` → `portVolbyVCVextended`**. Break one link and every downstream table breaks with it.

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

## 2. Quirks and traps, with what each would cost

1. **Why the holdings display shows 9 of 11.** The display cell hard-codes `n = 9` in `Table[..., {i, n}]`, so EURCash and 5yr UST (the two zero holdings) never appear; its loop also runs `i < Length[seclist]`, so position 11 never gets a currency symbol. The risk tables still include both positions. Python shows all 11.
2. **Duplicate security.** "10yr UST" is position 1 (Government, \$20mn) and position 3 (Swaps, \$30mn). Keying positions by name in a Python dict silently drops the first one and cuts reported volatility from \$616,900 to \$544,900, understating daily risk by 12%. Python gives each position its own index.
3. **Zero holdings still count.** EURCash and 5yr UST have DV01 of 0 but still put EURFX and USDYld5yr on the risk-factor list, and `volbySubPortfolio` zeroes holdings rather than dropping positions so every DV01 vector lines up.
4. **Empty category.** Commodity has no exposure: volatility 0, contribution the integer `0` (shown "0", not "0.0"), and a blank correlation because the code checks `zz > 0` before dividing.
5. **FX direction.** FX is quoted as foreign currency per dollar (GBPFX = 1/1.4) and PVs *divide* by it. Multiply instead and £10 million of cash is valued at \$7.1 million rather than \$14.0 million.
6. **Down bumps and the sign flip.** Yield DV01s are per 1bp *fall* and FX DV01s per 100% *fall*, so `populateVCV` multiplies each correlation by the two bump-unit signs. Skip the flip and portfolio volatility drops to \$431,300, understating risk by 30%.
7. **Two sets of mixture parameters.** `DistFn1.m` sets α = 0.05, β = 3; the notebook's `varsumm` quietly uses α = 0.01, β = 5. Trusting `DistFn1.m` reports a mixture VaR of \$2.22 million instead of \$1.68 million, overstating capital at risk by about a third.
8. **`eqtyFutpv` ignores bumped FX.** It reads the global `marketDataValues`, not its inputs, so futures never show FX risk. Kept on purpose.
9. **Dates.** `bondprc` inserts the settlement *year* into the maturity date to find the coupon dates, uses actual days for the stub period, and rounds the coupon count half to even. Five parameters means "swap."
10. **Stepwise selection.** `bestReplicatePort` is greedy with a strict `<`, so the first asset wins ties; `Ordering` is stable. With fewer than five risk factors the loop reuses a stale index and fails.
11. **Display rounding and indexing.** `NumberForm[x, {5, 0}]` switches to one-digit scientific notation at 10^6 ("4×10^7"), so those cells prove little. Lists are 1-based, and `corrmatrix` follows `marketDataNames` (18 items), not `riskFactorNames` (17 items).

A translation that matches one portfolio's rounded output may still be wrong. The open question is not whether a Python version can match these tables, but whether it can be shown to match on portfolios no one has seen yet.
