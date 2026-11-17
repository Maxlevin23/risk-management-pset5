"""One-command verification: Python tables versus the Mathematica reference.

    python verify.py

For the original portfolio and every file in ``scenarios/`` this script
  1. builds the nine outputs in Python and saves them under ``output/``,
  2. compares each one, cell by cell, with ``reference/<scenario>/tables.json``,
  3. prints one summary row per scenario and output, and
  4. writes ``output/verification_report.html`` with the Mathematica table next
     to the Python table and every mismatched cell highlighted.

Matching rule (from the assignment): same labels in the same places, and every
number, rounded the way the notebook rounds it, within ONE unit of the last
displayed digit.

A reference cell may be text as displayed by Mathematica (transcribed from the
notebook PDF) or a full-precision number exported by
``mathematica/RunScenarios.wl``; an exported number is first rounded to the
displayed precision.  A scenario with no ``tables.json`` is reported as
"NO REFERENCE": it has not been checked.

Exit code: 0 if nothing failed, 1 if any output failed.
"""

import html
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import formatting  # noqa: E402  (needs src/ on the path)
import tables_ch10  # noqa: E402

REFERENCE_DIR = PROJECT_DIR / "reference"
SCENARIO_DIR = PROJECT_DIR / "scenarios"
OUTPUT_DIR = PROJECT_DIR / "output"
# The notebook's holdings display stops after 9 rows; Python shows them all.
OUTPUTS_ALLOWING_EXTRA_ROWS = ("holdings",)


def parse_number(text):
    """Convert displayed text to a number.

    Args:
        text (str): e.g. "616,900", "(1,640,000)", "4×10^7", "-0.071".

    Returns:
        float | None: the value, or None if the text is not a number.
    """
    cleaned = text.strip().replace(",", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").replace("×10^", "e")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return -value if negative else value


def cell_status(python_cell, reference_cell):
    """Compare one Python cell with one Mathematica cell.

    Args:
        python_cell (tuple[str, float | None]): ``(text, unit)`` from formatting.
        reference_cell (str | float | int): displayed text, or an unrounded number.

    Returns:
        str: "exact" (same displayed value), "close" (differs by at most one
        unit in the last displayed digit) or "mismatch".
    """
    python_text, unit = python_cell
    if isinstance(reference_cell, str):
        if python_text.strip() == reference_cell.strip():
            return "exact"
        reference_value = parse_number(reference_cell)
    else:
        reference_value = float(reference_cell)
        if unit is not None:
            reference_value = round(reference_value / unit) * unit
    python_value = parse_number(python_text)
    if unit is None or python_value is None or reference_value is None:
        return "mismatch"
    difference = abs(python_value - reference_value)
    if difference <= unit * 1e-6:
        return "exact"
    return "close" if difference <= unit * (1 + 1e-6) else "mismatch"


def compare_grids(python_grid, reference_grid, allow_extra_rows=False):
    """Compare a Python display grid with a Mathematica reference grid.

    Args:
        python_grid (list[list[tuple]]): grid from ``formatting``.
        reference_grid (list[list]): reference rows of text or numbers.
        allow_extra_rows (bool): True if Python may have rows beyond the
            reference (only the holdings table, see module docstring).

    Returns:
        dict: ``compared`` (cells compared), ``matching`` (exact or close),
        ``close`` (matched only by the one-unit rule), ``passed`` (bool) and
        ``status`` (a grid of "exact"/"close"/"mismatch"/"missing" covering
        every row and column of either grid).
    """
    row_count = max(len(python_grid), len(reference_grid))
    status, compared, matching, close = [], 0, 0, 0
    for row in range(row_count):
        python_row = python_grid[row] if row < len(python_grid) else []
        reference_row = reference_grid[row] if row < len(reference_grid) else []
        status_row = []
        for column in range(max(len(python_row), len(reference_row))):
            if column >= len(python_row) or column >= len(reference_row):
                extra_python_row = allow_extra_rows and row >= len(reference_grid)
                result = "extra" if extra_python_row else "missing"
            else:
                result = cell_status(python_row[column], reference_row[column])
            if result != "extra":
                compared += 1
                matching += result in ("exact", "close")
                close += result == "close"
            status_row.append(result)
        status.append(status_row)
    return {"compared": compared, "matching": matching, "close": close,
            "passed": compared == matching, "status": status}


def load_reference(name):
    """Load the Mathematica tables of one scenario, if they exist.

    Args:
        name (str): scenario name ("original", "scenario1", ...).

    Returns:
        dict | None: output key -> reference grid, or None if there is no
        ``reference/<name>/tables.json``.
    """
    path = REFERENCE_DIR / name / "tables.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def verify_scenario(inputs_path):
    """Build, save and check the nine outputs of one scenario.

    Args:
        inputs_path (pathlib.Path | None): scenario file, or None for
            ``src/inputs.py``.

    Returns:
        dict: ``name``, ``grids`` (Python display grids), ``reference``
        (Mathematica grids or None) and ``results`` (output key -> comparison
        dict, or None when there is no reference).
    """
    inputs = tables_ch10.load_inputs(inputs_path)
    raw_tables = tables_ch10.build_raw_tables(inputs)
    grids = tables_ch10.format_tables(raw_tables)
    tables_ch10.save_tables(inputs["name"], raw_tables, grids, OUTPUT_DIR)
    reference = load_reference(inputs["name"])
    results = {}
    for key, _, _ in tables_ch10.OUTPUTS:
        if reference is None or key not in reference:
            results[key] = None
        else:
            results[key] = compare_grids(grids[key], reference[key],
                                         key in OUTPUTS_ALLOWING_EXTRA_ROWS)
    return {"name": inputs["name"], "grids": grids, "reference": reference,
            "results": results}


def summary_lines(scenarios):
    """Format the printed summary, one row per scenario and output.

    Args:
        scenarios (list[dict]): results of ``verify_scenario``.

    Returns:
        list[str]: lines of the summary table.
    """
    lines = [f"{'Scenario':<10} {'Output':<46} {'Cells compared':>14} "
             f"{'Cells matching':>14}  Pass/Fail",
             "-" * 100]
    for scenario in scenarios:
        for key, title, _ in tables_ch10.OUTPUTS:
            result = scenario["results"][key]
            if result is None:
                counts, verdict = f"{'-':>14} {'-':>14}", "NO REFERENCE"
            else:
                counts = f"{result['compared']:>14} {result['matching']:>14}"
                verdict = "PASS" if result["passed"] else "FAIL"
                if result["passed"] and result["close"]:
                    verdict += f" ({result['close']} within one unit)"
            lines.append(f"{scenario['name']:<10} {title:<46} {counts}  {verdict}")
    return lines


def html_table(rows, status, caption):
    """Render one grid as an HTML table with mismatches highlighted.

    Args:
        rows (list[list[str]]): cell texts.
        status (list[list[str]] | None): matching status per cell, or None.
        caption (str): table caption.

    Returns:
        str: HTML for the table.
    """
    parts = [f"<table><caption>{html.escape(caption)}</caption>"]
    for row_index, row in enumerate(rows):
        parts.append("<tr>")
        for column_index, text in enumerate(row):
            css = ""
            if status and row_index < len(status) and column_index < len(status[row_index]):
                css = status[row_index][column_index]
            parts.append(f'<td class="{css}">{html.escape(str(text))}</td>')
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


REPORT_STYLE = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;margin:24px;color:#1a1a1a}
h1{font-size:22px} h2{font-size:18px;margin-top:36px;border-bottom:2px solid #444}
h3{font-size:14px;margin:22px 0 6px}
pre{background:#f4f4f4;padding:10px;font-size:12px;overflow-x:auto}
.pair{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start}
table{border-collapse:collapse;font-size:12px;margin-bottom:8px}
caption{font-weight:600;text-align:left;padding-bottom:3px}
td{border:1px solid #bbb;padding:2px 7px;white-space:nowrap}
td.mismatch,td.missing{background:#f8b4b4;font-weight:700}
td.close{background:#fde9a8} td.extra{background:#e6e6e6}
.pass{color:#0a6b2d;font-weight:700}.fail{color:#b00020;font-weight:700}.noref{color:#8a5a00;font-weight:700}
"""


def reference_texts(grid, python_grid):
    """Show reference cells as displayed text (rounding exported numbers).

    Args:
        grid (list[list]): reference grid (text or unrounded numbers).
        python_grid (list[list[tuple]]): Python grid, used for the rounding unit.

    Returns:
        list[list[str]]: displayable reference grid.
    """
    rows = []
    for row_index, row in enumerate(grid):
        cells = []
        for column_index, cell in enumerate(row):
            if isinstance(cell, str):
                cells.append(cell)
                continue
            try:
                unit = python_grid[row_index][column_index][1]
            except IndexError:
                unit = None
            cells.append(f"{round(cell / unit) * unit:,.10g}" if unit else f"{cell:,.10g}")
        rows.append(cells)
    return rows


def write_html_report(scenarios, summary, path):
    """Write the side-by-side HTML verification report.

    Args:
        scenarios (list[dict]): results of ``verify_scenario``.
        summary (list[str]): lines from ``summary_lines``.
        path (pathlib.Path): file to write.

    Returns:
        pathlib.Path: the file written.
    """
    parts = ["<!doctype html><html><head><meta charset='utf-8'>",
             "<title>Problem 5 verification report</title>",
             f"<style>{REPORT_STYLE}</style></head><body>",
             "<h1>Problem 5: Python vs Mathematica verification report</h1>",
             "<p>Red = mismatch. Yellow = differs by one unit in the last displayed digit "
             "(accepted by the matching rule). Grey = Python rows beyond the notebook's "
             "9-row holdings display.</p>",
             "<pre>" + html.escape("\n".join(summary)) + "</pre>"]
    for scenario in scenarios:
        parts.append(f"<h2>Scenario: {html.escape(scenario['name'])}</h2>")
        for key, title, source in tables_ch10.OUTPUTS:
            result = scenario["results"][key]
            python_rows = formatting.grid_texts(scenario["grids"][key])
            if result is None:
                verdict = '<span class="noref">NO REFERENCE (not yet run in Mathematica)</span>'
            elif result["passed"]:
                verdict = (f'<span class="pass">PASS</span> '
                           f'{result["matching"]}/{result["compared"]} cells')
            else:
                verdict = (f'<span class="fail">FAIL</span> '
                           f'{result["matching"]}/{result["compared"]} cells')
            parts.append(f"<h3>{html.escape(title)} ({html.escape(source)}): {verdict}</h3>"
                         "<div class='pair'>")
            if result is not None:
                rows = reference_texts(scenario["reference"][key], scenario["grids"][key])
                parts.append(html_table(rows, None, "Mathematica"))
            parts.append(html_table(python_rows, result["status"] if result else None, "Python"))
            parts.append("</div>")
    parts.append("</body></html>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(parts), encoding="utf-8")
    return path


def main():
    """Run every scenario, print the summary and write the HTML report.

    Returns:
        int: 0 if no output failed, otherwise 1.
    """
    scenario_files = [None] + sorted(SCENARIO_DIR.glob("scenario*.py"))
    scenarios = [verify_scenario(path) for path in scenario_files]
    summary = summary_lines(scenarios)
    print("\n".join(summary))
    report = write_html_report(scenarios, summary, OUTPUT_DIR / "verification_report.html")
    (OUTPUT_DIR / "verification_summary.txt").write_text("\n".join(summary) + "\n",
                                                         encoding="utf-8")
    results = [result for scenario in scenarios for result in scenario["results"].values()]
    failed = sum(1 for result in results if result is not None and not result["passed"])
    unchecked = sum(1 for result in results if result is None)
    print(f"\n{failed} output(s) failed; {unchecked} output(s) have no Mathematica reference yet.")
    print(f"Side-by-side report: {report}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
