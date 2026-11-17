# Mathematica side

| File | What it is |
| --- | --- |
| `SamplePort2.m`, `DistFn1.m`, `Tables_Ch10.nb` | the originals, unmodified |
| `TableFunctions.wl` | the notebook's table functions copied out as plain text |
| `RunScenarios.wl` | runs every scenario and exports the reference values |
| `MakeScenarioNotebooks.wl` | builds each scenario's rerun notebook (`.nb`) and PDF in `reference/<scenario>/` |

Run `wolframscript -file mathematica/RunScenarios.wl` from the project folder.
It reads `reference/<scenario>/inputs.m` (and, for scenario 2,
`reference/scenario2/SamplePort2_scenario2.m`) and writes
`reference/<scenario>/tables.json` plus `reference/unit_values.json`.

`RunScenarios.wl` was run unchanged in Mathematica 15.0.1 (Wolfram Cloud) on
16 November 2026; that run produced the reference values now in `reference/`.
`MakeScenarioNotebooks.wl` was run there on 17 November 2026 with `CloudExport`
in place of `Export` (the cloud kernel writes to cloud files); the notebooks and
PDFs were copied into `reference/` and checked by SHA-256.
