"""Collect the project's source files into docs/Problem5_Code.md (for the code PDF)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = [
    ("Python: inputs and static data", ["src/inputs.py", "src/sampleport.py"]),
    ("Python: translation of DistFn1.m", ["src/distfn.py"]),
    ("Python: report functions, formatting and the tables script",
     ["src/reports.py", "src/formatting.py", "src/tables_ch10.py"]),
    ("Python: verification", ["verify.py"]),
    ("Python: scenario inputs",
     ["scenarios/scenario1.py", "scenarios/scenario2.py", "scenarios/scenario3.py"]),
    ("Python: tests",
     ["tests/conftest.py", "tests/helpers.py", "tests/test_pv_and_dv01.py",
      "tests/test_risk_and_distributions.py", "tests/test_tables.py", "tests/run_tests.py"]),
    ("Mathematica: scenario inputs and export script",
     ["reference/original/inputs.m", "reference/scenario1/inputs.m",
      "reference/scenario2/inputs.m", "reference/scenario3/inputs.m",
      "mathematica/RunScenarios.wl", "mathematica/MakeScenarioNotebooks.wl"]),
    ("Mathematica: table functions extracted from Tables_Ch10.nb",
     ["mathematica/TableFunctions.wl"]),
    ("Configuration", ["requirements.txt"]),
]
HEADER = '''---
title: "Problem 5: Code Listing (Python and Mathematica)"
subtitle: "PPHA 42525 Risk Management, Autumn 2026"
---

The original `SamplePort2.m`, `DistFn1.m` and `Tables_Ch10.nb` are unmodified and are in `mathematica/`; they are not repeated here. `reference/scenario2/SamplePort2_scenario2.m` is a copy of `SamplePort2.m` with two changed values (USDYld10yr .0253 to .0353; GBPFX 1/1.4 to 1/1.6).

'''


def language_of(path):
    """Return the syntax-highlighting language for a file name."""
    if path.endswith(".py"):
        return "python"
    return "mathematica" if path.endswith((".wl", ".m")) else "text"


def main():
    """Write docs/Problem5_Code.md."""
    parts = [HEADER, "| Section | Files |\n|---|---|\n"]
    for title, files in SECTIONS:
        parts.append(f"| {title} | {', '.join('`' + name + '`' for name in files)} |\n")
    for title, files in SECTIONS:
        parts.append(f"\n# {title}\n")
        for name in files:
            text = (ROOT / name).read_text(encoding="utf-8").rstrip()
            parts.append(f"\n## {name}\n\n````{language_of(name)}\n{text}\n````\n")
    (ROOT / "docs" / "Problem5_Code.md").write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
