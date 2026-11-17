"""Python version of Tables_Ch10.nb: build and save the nine outputs.

Run from the project folder:

    python src/tables_ch10.py                         # original portfolio (src/inputs.py)
    python src/tables_ch10.py scenarios/scenario1.py  # any scenario file

For each output this writes, under ``output/<scenario name>/``:
    NN_<name>.csv   raw, full-precision numbers
    NN_<name>.txt   formatted the way the notebook displays it
and one ``all_tables.md`` with all nine formatted tables.

Like the notebook, this is a script: it sets up the portfolio and calls the
report functions.  It never reads anything in ``reference/``.
"""

import runpy
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SOURCE_DIR.parent
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import formatting  # noqa: E402  (needs SOURCE_DIR on the path)
import reports  # noqa: E402
import sampleport  # noqa: E402

# (key, title, notebook source) for the nine outputs, in the assignment's order.
OUTPUTS = [
    ("holdings", "1. Holdings table", "Out[38]"),
    ("table1", "2. Table 1: Securities, risk factors, DV01s", "displayRF"),
    ("category", "3. Risk-category summary", "reportFunction1[[1]]"),
    ("top_contributors", "4. Top three contributors", "reportFunction1[[2]]"),
    ("single_hedge", "5. Best single hedge", "reportFunction1[[3]]"),
    ("best_hedges", "6. Top three best hedges", "reportFunction1[[4]]"),
    ("replicating", "7. Best replicating portfolios", "reportFunction1[[5]]"),
    ("subportfolio", "8. Volatility by subportfolio", "volbySubPortfolio"),
    ("var", "9. VaR summary", "varsumm"),
]

FORMATTERS = {
    "holdings": formatting.format_holdings,
    "table1": formatting.format_displayRF,
    "category": formatting.format_vol_summary,
    "top_contributors": formatting.format_contributors,
    "single_hedge": formatting.format_contributors,
    "best_hedges": formatting.format_contributors,
    "replicating": formatting.format_replicating,
    "subportfolio": formatting.format_vol_summary,
    "var": formatting.format_varsumm,
}

REQUIRED_INPUT_NAMES = ("SECLIST", "HOLDINGS", "SUBPORTFOLIO", "SETTLEDATE")


def load_inputs(inputs_path=None):
    """Read the portfolio inputs from ``src/inputs.py`` or a scenario file.

    Args:
        inputs_path (str | pathlib.Path | None): a Python file defining
            SECLIST, HOLDINGS, SUBPORTFOLIO, SETTLEDATE and (optionally)
            MARKET_DATA_OVERRIDES.  None means ``src/inputs.py``.

    Returns:
        dict: keys ``name``, ``seclist``, ``holdings``, ``subportfolio``,
        ``settledate`` and ``market_data_overrides``.

    Raises:
        ValueError: if a required name is missing or the three position lists
            have different lengths.
    """
    path = Path(inputs_path) if inputs_path else SOURCE_DIR / "inputs.py"
    namespace = runpy.run_path(str(path))
    missing = [name for name in REQUIRED_INPUT_NAMES if name not in namespace]
    if missing:
        raise ValueError(f"{path} does not define {missing}")
    lengths = {len(namespace[name]) for name in REQUIRED_INPUT_NAMES[:3]}
    if len(lengths) != 1:
        raise ValueError(f"{path}: SECLIST, HOLDINGS and SUBPORTFOLIO differ in length")
    return {
        "name": "original" if inputs_path is None else path.stem,
        "seclist": list(namespace["SECLIST"]),
        "holdings": list(namespace["HOLDINGS"]),
        "subportfolio": list(namespace["SUBPORTFOLIO"]),
        "settledate": list(namespace["SETTLEDATE"]),
        "market_data_overrides": dict(namespace.get("MARKET_DATA_OVERRIDES", {})),
    }


def build_raw_tables(inputs):
    """Compute the nine raw tables for one set of inputs.

    Args:
        inputs (dict): result of ``load_inputs``.

    Returns:
        dict[str, pandas.DataFrame]: raw (unrounded) table for each key in
        ``OUTPUTS``.
    """
    data = sampleport.load_data(inputs["market_data_overrides"])
    seclist, holdings = inputs["seclist"], inputs["holdings"]
    settledate, subportfolio = inputs["settledate"], inputs["subportfolio"]
    report = reports.reportFunction1(seclist, holdings, settledate, data)
    return {
        "holdings": reports.holdings_table(seclist, holdings, subportfolio, data),
        "table1": reports.displayRF(seclist, holdings, settledate, data),
        "category": report[0],
        "top_contributors": report[1],
        "single_hedge": report[2],
        "best_hedges": report[3],
        "replicating": report[4],
        "subportfolio": reports.volbySubPortfolio(seclist, holdings, settledate,
                                                  subportfolio, data),
        "var": reports.varsumm(seclist, holdings, settledate, data),
    }


def format_tables(raw_tables):
    """Round and lay out every raw table the way the notebook displays it.

    Args:
        raw_tables (dict[str, pandas.DataFrame]): result of ``build_raw_tables``.

    Returns:
        dict[str, list[list[tuple]]]: display grid for each output key.
    """
    return {key: FORMATTERS[key](raw_tables[key]) for key, _, _ in OUTPUTS}


def save_tables(name, raw_tables, grids, output_dir=None):
    """Write raw CSVs and formatted text/Markdown for one scenario.

    Args:
        name (str): scenario name; files go to ``output/<name>/``.
        raw_tables (dict[str, pandas.DataFrame]): raw tables.
        grids (dict[str, list]): formatted display grids.
        output_dir (pathlib.Path | None): parent folder; default ``output/``.

    Returns:
        pathlib.Path: the folder written to.
    """
    folder = (Path(output_dir) if output_dir else PROJECT_DIR / "output") / name
    folder.mkdir(parents=True, exist_ok=True)
    markdown = [f"# Tables_Ch10 in Python: {name}\n"]
    for number, (key, title, source) in enumerate(OUTPUTS, start=1):
        stem = f"{number:02d}_{key}"
        raw_tables[key].to_csv(folder / f"{stem}.csv", index=False, float_format="%.10g")
        (folder / f"{stem}.txt").write_text(formatting.grid_to_text(grids[key]) + "\n",
                                            encoding="utf-8")
        markdown.append(f"## {title}\n\nNotebook source: `{source}`\n\n"
                        + formatting.grid_to_markdown(grids[key]) + "\n")
    (folder / "all_tables.md").write_text("\n".join(markdown), encoding="utf-8")
    return folder


def main(arguments):
    """Build, print and save the nine outputs.

    Args:
        arguments (list[str]): command-line arguments; an optional first item
            is the path of a scenario inputs file.

    Returns:
        int: 0 on success (process exit code).
    """
    inputs = load_inputs(arguments[0] if arguments else None)
    raw_tables = build_raw_tables(inputs)
    grids = format_tables(raw_tables)
    for key, title, _ in OUTPUTS:
        print(f"\n{title}\n" + formatting.grid_to_text(grids[key]))
    folder = save_tables(inputs["name"], raw_tables, grids)
    print(f"\nSaved raw CSVs and formatted tables to {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
