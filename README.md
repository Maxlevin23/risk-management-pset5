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
| original | notebook portfolio | displayed values transcribed from the notebook PDF | 9 of 9 outputs pass, 506 of 506 cells (1 by the one-unit rule) |
| scenario1 | portfolio changes | **not yet produced** | Python runs; not yet compared |
| scenario2 | market-data change | **not yet produced** | Python runs; not yet compared |
| scenario3 | new securities and settle date | **not yet produced** | Python runs; not yet compared |

The scenario references need Mathematica, which was not available on the machine
where the Python was written. To produce them, run once:

```bash
wolframscript -file mathematica/RunScenarios.wl
```

This writes `reference/scenario*/tables.json` and `reference/unit_values.json`;
`python verify.py` then compares all four scenarios, and the two tests that
currently report SKIPPED start checking. See "To finish before submitting" below.

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

## Known remaining discrepancy

One cell, Table 1, FTE Equity, EURFX DV01: Mathematica shows `6×10^6`, Python
shows `7×10^6`. The true value is exactly 6,500,000 and the display keeps one
digit, so floating-point noise of about 1e-8 decides the rounding. This is the
"value on a rounding boundary" case the assignment allows (one unit in the last
displayed digit). The neighbouring FTEEqSpecific DV01, also 6,500,000, shows
`7×10^6` in both.

## To finish before submitting

1. Run `wolframscript -file mathematica/RunScenarios.wl` (needs Mathematica),
   then `python verify.py`, and paste the new summary into the report.
2. For each scenario, apply `reference/<scenario>/inputs.m` to a copy of
   `Tables_Ch10.nb` (scenario 2 also loads `SamplePort2_scenario2.m`), evaluate,
   and save the notebook PDF into `reference/<scenario>/`.

The checkpoint is on the branch `bionic/checkpoint`; later work is on `main`.
