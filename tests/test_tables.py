"""Table tests: the nine outputs against the Mathematica reference, plus
scenario checks and optional full-precision checks.

``reference/unit_values.json`` and the scenario ``tables.json`` files are
written by ``mathematica/RunScenarios.wl``.  Tests that need a file that does
not exist yet report "SKIPPED" instead of passing silently.
"""

import json

import numpy as np

import conftest
import distfn
import tables_ch10
import verify
from helpers import HOLDINGS, SECLIST, SETTLEDATE, fresh_data

SCENARIO_DIR = conftest.PROJECT_DIR / "scenarios"
UNIT_VALUES = conftest.PROJECT_DIR / "reference" / "unit_values.json"


def skip(reason):
    """Skip under pytest; print a notice under the plain runner."""
    try:
        import pytest
    except ImportError:
        print(f"      SKIPPED: {reason}")
        return
    pytest.skip(reason)


def build(path=None):
    """Build raw tables and display grids for one inputs file."""
    inputs = tables_ch10.load_inputs(path)
    raw = tables_ch10.build_raw_tables(inputs)
    return inputs, raw, tables_ch10.format_tables(raw)


def test_all_nine_outputs_match_the_notebook_pdf():
    _, _, grids = build()
    reference = verify.load_reference("original")
    for key, title, _ in tables_ch10.OUTPUTS:
        result = verify.compare_grids(grids[key], reference[key], key == "holdings")
        assert result["passed"], f"{title}: {result['matching']}/{result['compared']} cells"


def test_holdings_table_shows_all_eleven_positions():
    _, raw, _ = build()
    assert len(raw["holdings"]) == 11
    assert list(raw["holdings"]["Position"]) == list(range(1, 12))
    assert raw["holdings"]["Curr"].iloc[-1] == "$"       # notebook loop never reaches row 11


def test_comparison_rule_accepts_one_unit_and_rejects_two():
    assert verify.cell_status(("616,900", 100.0), "616,900") == "exact"
    assert verify.cell_status(("616,900", 100.0), "617,000") == "close"
    assert verify.cell_status(("616,900", 100.0), "617,100") == "mismatch"
    assert verify.cell_status(("7×10^6", 1e6), "6×10^6") == "close"
    assert verify.cell_status(("(1,640,000)", 1000.0), -1640184.8) == "exact"
    assert verify.cell_status(("GBPFX", None), "EURFX") == "mismatch"
    assert verify.cell_status(("", None), "") == "exact"


def test_a_wrong_reference_cell_is_detected():
    _, _, grids = build()
    reference = verify.load_reference("original")
    tampered = json.loads(json.dumps(reference["category"]))
    tampered[2][1] = "345,600"                           # true value 345,800
    assert not verify.compare_grids(grids["category"], tampered)["passed"]


def test_every_scenario_runs_and_is_internally_consistent():
    for path in sorted(SCENARIO_DIR.glob("scenario*.py")):
        inputs, raw, grids = build(path)
        assert len(raw["holdings"]) == len(inputs["seclist"])
        assert set(grids) == {key for key, _, _ in tables_ch10.OUTPUTS}
        category = raw["category"]
        assert abs(category["Contribution"][1:].sum() - 100) < 1e-8
        assert abs(raw["subportfolio"]["Contribution"][1:].sum() - 100) < 1e-8
        assert raw["var"]["Value"][0] > 0 > raw["var"]["Value"][1]


def test_scenario3_offsetting_duplicates_cancel_only_in_total():
    inputs, raw, _ = build(SCENARIO_DIR / "scenario3.py")
    without = [h for s, h in zip(inputs["seclist"], inputs["holdings"]) if s != "10yr UST"]
    names = [s for s in inputs["seclist"] if s != "10yr UST"]
    data = fresh_data()
    total = distfn.portVolbyVCV(inputs["seclist"], inputs["holdings"], inputs["settledate"], data)
    assert abs(total - distfn.portVolbyVCV(names, without, inputs["settledate"], data)) < 1e-6
    table1 = raw["table1"]
    ust = table1[table1["Security"] == "10yr UST"]
    assert list(ust["Position"]) == [2, 3] and abs(ust["DV01"].sum()) < 1e-9
    assert ust["DV01"].abs().min() > 1000


def test_market_data_override_changes_only_the_copy():
    inputs, _, _ = build(SCENARIO_DIR / "scenario2.py")
    assert inputs["market_data_overrides"]["GBPFX"] == 1 / 1.6
    data = fresh_data()
    assert data["marketDataValues"][data["marketDataNames"].index("GBPFX")] == 1 / 1.4


def test_scenarios_match_mathematica_exports():
    checked = 0
    for path in sorted(SCENARIO_DIR.glob("scenario*.py")):
        reference = verify.load_reference(path.stem)
        if reference is None:
            continue
        _, _, grids = build(path)
        for key, title, _ in tables_ch10.OUTPUTS:
            result = verify.compare_grids(grids[key], reference[key], key == "holdings")
            assert result["passed"], f"{path.stem} {title}"
        checked += 1
    if checked == 0:
        skip("no scenario tables.json yet: run mathematica/RunScenarios.wl")


def test_function_values_match_mathematica_at_full_precision():
    if not UNIT_VALUES.exists():
        skip("reference/unit_values.json not found: run mathematica/RunScenarios.wl")
        return
    expected = json.loads(UNIT_VALUES.read_text())
    data = fresh_data()
    result = distfn.portVolbyVCVextended(SECLIST, HOLDINGS, SETTLEDATE, data)
    _, _, sec_dv01s = distfn.populateSecDV01s(SECLIST, HOLDINGS, SETTLEDATE, data)

    def same(actual, wanted):
        return np.allclose(np.asarray(actual, dtype=float), np.asarray(wanted, dtype=float),
                           rtol=1e-8, atol=1e-6)

    assert distfn.serialday(SETTLEDATE) == expected["serialday_settle"]
    assert same(distfn.bondprc(0.0253, SETTLEDATE, data["secParmValues"][1]), expected["bondprc_10yrUST"])
    assert same(distfn.pvPort(SECLIST, HOLDINGS, SETTLEDATE, data["marketDataValues"], data),
                expected["pvPort"])
    assert same([v for row in sec_dv01s for v in row], [v for row in expected["secDV01s"] for v in row])
    assert result["rflist"] == expected["portDV01Names"]
    for key, name in (("portdv01s", "portDV01s"), ("vcv", "vcv"), ("mcp", "mcp"),
                      ("contallornot", "contallornot"), ("besthedge", "besthedge"),
                      ("volbesthedge", "volbesthedge"), ("corr", "corr"), ("repport", "repport")):
        assert same(result[key], expected[name]), name
    assert same(distfn.cdf(distfn.normalmix(1.0), -2.0), expected["mix_cdf"])
    assert same(distfn.quantile(distfn.normalmix(1.0), 0.01), expected["mix_quantile"])
    assert same(distfn.var(distfn.student, 1 / 255, 1.0), expected["var_student"])
