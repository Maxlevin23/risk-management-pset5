# Mathematica side

| File | What it is |
| --- | --- |
| `SamplePort2.m`, `DistFn1.m`, `Tables_Ch10.nb` | the originals, unmodified |
| `TableFunctions.wl` | the notebook's table functions copied out as plain text |
| `RunScenarios.wl` | runs every scenario and exports the reference values |

Run `wolframscript -file mathematica/RunScenarios.wl` from the project folder.
It reads `reference/<scenario>/inputs.m` (and, for scenario 2,
`reference/scenario2/SamplePort2_scenario2.m`) and writes
`reference/<scenario>/tables.json` plus `reference/unit_values.json`.

Both `.wl` files were run unchanged in Mathematica 15.0.1 (Wolfram Cloud) on
16 November 2026; that run produced the reference files now in `reference/`.
