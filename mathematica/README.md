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

These two `.wl` files were written without access to a Mathematica kernel and
have not been executed yet; if one fails to load, the error will point at the
line to fix.
