# Problem 5: Chapter 10 risk reports, Mathematica to Python

PPHA 42525 Risk Management, Autumn 2026. Python translation of `Tables_Ch10.nb`,
`DistFn1.m` and `SamplePort2.m`, with a one-command check against Mathematica.

## Install and run

```bash
python -m pip install -r requirements.txt   # Python 3.15, numpy 2.5.4, pandas 3.0.6
python verify.py                            # build all tables, compare, write the report
python tests/run_tests.py                   # unit and table tests (or: python -m pytest)
python src/tables_ch10.py                   # just print and save the nine tables
python src/tables_ch10.py scenarios/scenario1.py
```

`verify.py` prints one row per scenario and output (cells compared, cells
matching, pass/fail) and writes `output/verification_report.html`, which shows
each Mathematica table beside its Python counterpart with mismatches in red.

## Current verification status

| Scenario | What it is | Mathematica reference | Result |
| --- | --- | --- | --- |
| original | notebook portfolio | displayed values transcribed from the notebook PDF | 9 of 9 outputs pass, 506 of 506 cells |
| scenario1 | portfolio changes | full-precision export from Mathematica 15.0.1 | 9 of 9 outputs pass, 514 of 514 cells |
| scenario2 | market-data change | full-precision export from Mathematica 15.0.1 | 9 of 9 outputs pass, 514 of 514 cells |
| scenario3 | new securities and settle date | full-precision export from Mathematica 15.0.1 | 9 of 9 outputs pass, 570 of 570 cells |

Every one of the 2,104 cells shows the identical displayed value; none needs the
one-unit tolerance. All 61 tests pass, including 21 that compare each translated function
with Mathematica at full precision (`tests/test_distfn_vs_mathematica.py`).

The scenario references were produced by running `mathematica/RunScenarios.wl`
in Wolfram Cloud. To regenerate them with a local Mathematica:

```bash
wolframscript -file mathematica/RunScenarios.wl
```

## Layout

```
README.md            this file
requirements.txt     exact package versions
verify.py            one-command verification
src/
  inputs.py          THE one place for seclist, holdings, subportfolio, settledate
  sampleport.py      SamplePort2.m lists (static and market data)
  distfn.py          DistFn1.m functions (PV, DV01, VCV, risk, distributions)
  reports.py         notebook report functions; return raw floats only
  formatting.py      NumberForm / AccountingForm rounding and table layout
  tables_ch10.py     script: builds and saves the nine outputs
scenarios/           Python inputs for each test scenario
tests/               unit tests and table tests
reference/           Mathematica inputs, PDFs and table values per scenario
mathematica/         original .m/.nb files, extracted table functions, export script
output/              generated tables (CSV raw, TXT/MD formatted) and the HTML report
docs/                Part I map and quirks, 2-page report, AI appendix, code listing
```

Computation and formatting are separate: every function in `reports.py`
returns a DataFrame of unrounded floats (saved as CSV); `formatting.py`
rounds and lays them out. Production code never reads `reference/`.

## Function-mapping table

| Mathematica (file) | Python | Notes |
| --- | --- | --- |
| `serialday` (DistFn1.m) | `distfn.serialday` | days since 1900-01-01, plus 2 |
| `DatePlus[..., "Month"]` (built in) | `distfn.date_plus_months` | clamps to month end |
| `pv` | `distfn.pv` | |
| `bondprc` | `distfn.bondprc`, `distfn.coupon_dates_around` | `Which` block is the helper |
| `bondpv` | `distfn.bondpv` | |
| `swappv` | `distfn.swappv` | |
| `swappvactual` | `distfn.swappvactual` | used by `Swap201901` (scenario 3) |
| `bondoptionprc`, `bondoptionpv` | `distfn.bondoptionprc`, `distfn.bondoptionpv` | |
| `simpCDSpv` | `distfn.simpCDSpv` | |
| `cashpv` | `distfn.cashpv` | |
| `eqtypv` | `distfn.eqtypv` | |
| `eqtyFutpv` | `distfn.eqtyFutpv` | keeps the unbumped-FX quirk |
| `secPVFunction` (symbols) | `distfn.PV_FUNCTIONS` (name to function) | |
| `pickSecRFfn` | `distfn.pickSecRFfn` | |
| `fxrateSec`, `fxsymb` | `distfn.fxrateSec`, `distfn.fxsymb` | |
| `pvposn`, `pvPort` | `distfn.pvposn`, `distfn.pvPort` | |
| `populateSecDV01s` | `distfn.populateSecDV01s`, `distfn.bump_market_data` | positions kept by index |
| `populatePortDV01s` | `distfn.populatePortDV01s` | |
| `populateEqvDV01s` | `distfn.populateEqvDV01s` | |
| `populateVCV` | `distfn.populateVCV` | sign flip for down bumps |
| `secVolbyVCV`, `rfVolbyVCV` | `distfn.secVolbyVCV`, `distfn.rfVolbyVCV` | |
| `portVolbyVCV` | `distfn.portVolbyVCV` | |
| `portVolbyVCVextended` | `distfn.portVolbyVCVextended` | 13-item list becomes a dict |
| `pdf`, `cdf`, `quantile` | `distfn.pdf`, `distfn.cdf`, `distfn.quantile` | `FindRoot` becomes safeguarded Newton |
| `var`, `normal`, `student`, `normalmix` | `distfn.var`, `distfn.normal`, `distfn.student`, `distfn.normalmix` | |
| `StudentTDistribution` quantile (built in) | `distfn.standard_student_cdf` + root find | no SciPy needed |
| Out[38] holdings `Module` (notebook) | `reports.holdings_table` | all positions, not 9 |
| `displayRF` (notebook) | `reports.displayRF` + `formatting.format_displayRF` | |
| `reportFunction1` (notebook) | `reports.reportFunction1`, `reports.category_summary` | |
| `tableContributers` (notebook) | `reports.tableContributers` + `formatting.format_contributors` | |
| `bestReplicatePort` (notebook) | `reports.bestReplicatePort`, `reports.best_next_asset` | |
| `volbySubPortfolio` (notebook) | `reports.volbySubPortfolio` | |
| `varsumm` (notebook) | `reports.varsumm` | alpha = 1%, beta = 5 |
| `Ordering`, `Union` (built in) | `reports.mathematica_ordering`, `reports.mathematica_union` | stable ties; sorted labels |
| `NumberForm[x, {n, f}]` | `formatting.number_form` | scientific at 10^6 |
| `AccountingForm[x, {n, 0}]` | `formatting.accounting_form` | negatives in parentheses |
| SamplePort2.m lists | `sampleport.py` (same names), `sampleport.load_data` | |

Not translated because none of the nine outputs uses them: `dateday`,
`bondprcSimp`, `futpv`, `dv01posn`, `dv01sec`, `pvposnold`,
`populateSecDV01sOld`, `calcSimulatedPL`, `detailtable`, and the
`"levelcurveinp"` branch of `populateSecDV01s` (it calls `bootstrapcurve`,
which is not defined in the files provided).

## How sampleport.py was produced

The lists were converted from `SamplePort2.m` by a script (braces to brackets,
precision backticks removed), not retyped, so the 18 x 18 correlation matrix
and the volatilities are character-for-character the Mathematica values.

## A discrepancy that was found and resolved

In Table 1, FTE Equity has two DV01s that are both 6,500,000 to within 1e-8 but
display as `7×10^6` (FTEEqSpecific) and `6×10^6` (EURFX), because the display keeps
one digit. Python first showed `7×10^6` for both. Mathematica evaluates
`holding*1000000*x/fx` as (exact integer product) × (x × fx⁻¹); `eqtypv` and
`eqtyFutpv` now use that order and reproduce Mathematica's values to the last bit.

## Rerun scenario notebooks

Each `reference/<scenario>/` folder holds `Tables_Ch10_<scenario>.nb` and
`Tables_Ch10_<scenario>.pdf`: the scenario's changed inputs and the nine tables
as drawn by the original Mathematica code (built by
`mathematica/MakeScenarioNotebooks.wl` in Mathematica 15.0.1, Wolfram Cloud).
Every number in the Python tables appears, in the same order, in these PDFs.

The checkpoint is on the branch `bionic/checkpoint`; later work is on `main`.
