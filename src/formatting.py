"""Display layer: round and lay out the raw tables the way the notebook does.

``reports.py`` returns raw floats; this module turns them into grids of text
that match the notebook's ``Grid[...]`` output cell for cell.

A grid is a list of rows; a row is a list of cells; a cell is a tuple
``(text, unit)``.  ``unit`` is the size of one unit in the last displayed
digit (e.g. 100 for "616,900", 0.1 for "39.2") and is None for a label.
``verify.py`` uses ``unit`` for the "one unit in the last displayed digit"
matching rule.

Mathematica formats translated here:
    NumberForm[x, {n, f}]      -> number_form(x, n, f)
    AccountingForm[x, {n, 0}]  -> accounting_form(x, n)
"""

from decimal import ROUND_HALF_EVEN, Decimal

import pandas as pd

LABEL_UNIT = None
BLANK = ("", LABEL_UNIT)


def label(text):
    """Return a text-only cell (no numeric tolerance)."""
    return (str(text), LABEL_UNIT)


def round_for_display(value, digits, decimals):
    """Round once, to the coarser of ``digits`` significant figures or ``decimals`` places.

    Rounding once matters: 0.025365051 shown with 5 decimals is 0.02537, but
    rounding to 5 significant figures first (0.025365) and then to 5 decimals
    would give 0.02536.

    Args:
        value (float): number to round (not zero).
        digits (int): maximum significant figures.
        decimals (int): maximum figures after the decimal point.

    Returns:
        tuple[decimal.Decimal, int, int]: ``(rounded value, its base-10
        exponent, places kept after the point)``; places is negative when
        rounding to tens, hundreds, ...
    """
    exact = Decimal(repr(float(value)))
    exponent = exact.adjusted()
    for _ in range(2):  # a second pass handles 999.96 -> 1000.0
        places = min(decimals, digits - 1 - exponent)
        rounded = exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
        if rounded == 0 or rounded.adjusted() == exponent:
            break
        exponent = rounded.adjusted()
    return rounded, exponent, places


def number_form(value, digits, decimals, digit_block=False):
    """Translate ``NumberForm[value, {digits, decimals}]``.

    Mathematica shows at most ``digits`` significant figures and ``decimals``
    figures after the point, and switches to scientific notation at 10^6
    (which is why some Table 1 DV01s display as "4×10^7").

    Args:
        value (float): number to display; NaN/None displays as blank.
        digits (int): significant figures.
        decimals (int): figures after the decimal point.
        digit_block (bool): True to add thousands separators.

    Returns:
        tuple[str, float | None]: a ``(text, unit)`` cell.
    """
    if value is None or pd.isna(value):
        return BLANK
    if value == 0:
        return ("0", 10.0 ** -decimals)
    rounded, exponent, places = round_for_display(value, digits, decimals)
    if exponent >= 6:
        mantissa = Decimal(repr(float(value))).scaleb(-exponent)
        mantissa = mantissa.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
        if abs(mantissa) >= 10:
            mantissa, exponent = mantissa / 10, exponent + 1
        return (f"{mantissa:.{decimals}f}×10^{exponent}", 10.0 ** (exponent - decimals))
    separator = "," if digit_block else ""
    return (f"{rounded:{separator}.{max(places, 0)}f}", 10.0 ** -places)


def accounting_form(value, digits=4):
    """Translate ``AccountingForm[value, {digits, 0}, DigitBlock -> 3]``.

    Rounds to ``digits`` significant figures (and no decimals), adds thousands
    separators, never uses scientific notation and shows negatives in
    parentheses.

    Args:
        value (float): number to display; NaN/None displays as blank.
        digits (int): significant figures.

    Returns:
        tuple[str, float | None]: a ``(text, unit)`` cell.
    """
    if value is None or pd.isna(value):
        return BLANK
    if value == 0:
        return ("0", 1.0)
    rounded, _, places = round_for_display(value, digits, 0)
    text = f"{abs(rounded):,.0f}"
    if rounded < 0:
        text = f"({text})"
    return (text, 10.0 ** -places)


def notional_text(symbol, holding):
    """Translate ``symbol <> ToString[holding] <> "mn"``, e.g. "$-20mn".

    Args:
        symbol (str): currency symbol.
        holding (float): amount in millions.

    Returns:
        str: the notional label; whole numbers print without a decimal point.
    """
    amount = int(holding) if float(holding).is_integer() else holding
    return f"{symbol}{amount}mn"


def format_holdings(raw):
    """Lay out output 1 (holdings table) from ``reports.holdings_table``.

    Args:
        raw (pandas.DataFrame): raw holdings table.

    Returns:
        list[list[tuple]]: header row then one row per position.
    """
    grid = [[label("Security"), label("Amount (mn local)"), label("Curr"),
             label("Subportfolio")]]
    for row in raw.itertuples(index=False):
        amount = row[2]
        amount_text = str(int(amount)) if float(amount).is_integer() else str(amount)
        grid.append([label(row[1]), (amount_text, 1.0), label(row[3]), label(row[4])])
    return grid


def format_displayRF(raw):
    """Lay out output 2 (Table 1) from ``reports.displayRF``.

    Each position gets a heading row (name, notional, security vol) followed
    by one row per risk factor, exactly as the notebook's ``displayRF``.

    Args:
        raw (pandas.DataFrame): raw Table 1, one row per (position, risk factor).

    Returns:
        list[list[tuple]]: the display grid.
    """
    grid = [[label(text) for text in ("Security", "Notional", "Security Vol", "RIsk Factor",
                                      "DV01", "DV01 units", "RF unit Vol", "RF pos'n Vol")]]
    for _, position_rows in raw.groupby("Position", sort=True):
        first = position_rows.iloc[0]
        grid.append([label(first["Security"]),
                     label(notional_text(first["Curr"], first["Notional"])),
                     number_form(first["Security Vol"], 4, 0, digit_block=True),
                     BLANK, BLANK, BLANK, BLANK, BLANK])
        for _, row in position_rows.iterrows():
            vol_format = (5, 5) if row["DV01 units"] == "percent" else (4, 3)
            grid.append([BLANK, BLANK, BLANK, label(row["Risk Factor"]),
                         number_form(row["DV01"], 5, 0, digit_block=True),
                         label(row["DV01 units"]),
                         number_form(row["RF unit Vol"], *vol_format),
                         number_form(row["RF pos'n Vol"], 4, 0, digit_block=True)])
    return grid


def format_vol_summary(raw):
    """Lay out outputs 3 and 8 (volatility by category / by subportfolio).

    Args:
        raw (pandas.DataFrame): raw table whose first row is "Overall" and
            whose columns are (label, Exp Vol, Contribution, Correlation).

    Returns:
        list[list[tuple]]: the display grid.  As in the notebook, the
        "Overall" row shows the fixed texts "100.0" and "with portfolio".
    """
    grid = [[BLANK, label("Exp Vol ($)"), label("Contribution"), label("Correlation")]]
    for position, row in enumerate(raw.itertuples(index=False)):
        if position == 0:
            grid.append([label(row[0]), accounting_form(row[1]), ("100.0", 0.1),
                         label("with portfolio")])
        else:
            grid.append([label(row[0]), accounting_form(row[1]),
                         number_form(row[2], 4, 1), number_form(row[3], 4, 3)])
    return grid


def format_contributors(raw):
    """Lay out outputs 4, 5 and 6 from ``reports.tableContributers``.

    Args:
        raw (pandas.DataFrame): raw contributors table.

    Returns:
        list[list[tuple]]: two heading rows then one row per risk factor.
    """
    grid = [[label(text) for text in ("", "Exp Vol", "", "Curr Pos'n", "Trade to best",
                                      "% Reduction in Vol to", "")],
            [label(text) for text in ("", "(1-sig P&L)", "Contribution", "(mn eqv)",
                                      "Hedge (eqv)", "Best Hedge", "Zero Pos'n")]]
    for row in raw.itertuples(index=False):
        grid.append([label(row[0]), accounting_form(row[1])]
                    + [number_form(value, 4, 1) for value in row[2:]])
    return grid


def replicating_cell_pair(raw, size, slot):
    """Helper for ``format_replicating``: (asset name, eqv position) cells.

    Args:
        raw (pandas.DataFrame): raw replicating-portfolio table.
        size (int): portfolio size (1, 3 or 5).
        slot (int): which asset of that portfolio (1-based).

    Returns:
        list[tuple]: two cells; blank if that portfolio or slot does not exist.
    """
    rows = raw[raw["Assets"] == size]
    if rows.empty or slot > size:
        return [BLANK, BLANK]
    row = rows.iloc[0]
    return [label(row[f"Asset {slot}"]), number_form(row[f"Eqv Pos'n {slot}"], 4, 1)]


def format_replicating(raw):
    """Lay out output 7 (best replicating portfolios) for 1, 3 and 5 assets.

    Args:
        raw (pandas.DataFrame): raw table from ``reports.bestReplicatePort``.

    Returns:
        list[list[tuple]]: the nine-row display grid used by the notebook.
    """
    sizes = (1, 3, 5)
    explained = [label("%Var / %Vol Explained")]
    for size in sizes:
        rows = raw[raw["Assets"] == size]
        values = (rows.iloc[0]["% Var"], rows.iloc[0]["% Vol"]) if not rows.empty else (None, None)
        explained += [number_form(values[0], 4, 1), number_form(values[1], 4, 1)]
    grid = [
        [label(text) for text in ("", "One Asset", "", "Three Assets", "", "Five Assets", "")],
        [label(text) for text in ("", "% Var", "% Vol", "% Var", "% Vol", "% Var", "% Vol")],
        explained,
        [label(text) for text in ("", "Asset", "Eqv Pos'n", "Asset", "Eqv Pos'n",
                                  "Asset", "Eqv Pos'n")],
    ]
    for slot in range(1, 6):
        row = [label("Asset / Eqv Pos'n") if slot == 1 else BLANK]
        for size in sizes:
            row += replicating_cell_pair(raw, size, slot)
        grid.append(row)
    return grid


def format_varsumm(raw):
    """Lay out output 9 (VaR summary) from ``reports.varsumm``.

    Args:
        raw (pandas.DataFrame): raw table with columns ``Measure`` and ``Value``.

    Returns:
        list[list[tuple]]: title row then one row per measure; negative VaR
        values appear in parentheses.
    """
    grid = [[label("VOLATILITY and 1-ot-of 255 VaR"), BLANK]]
    for row in raw.itertuples(index=False):
        grid.append([label(row[0]), accounting_form(row[1])])
    return grid


def grid_texts(grid):
    """Strip the tolerance information from a grid.

    Args:
        grid (list[list[tuple]]): display grid of ``(text, unit)`` cells.

    Returns:
        list[list[str]]: the same grid holding only the text of each cell.
    """
    return [[cell[0] for cell in row] for row in grid]


def grid_to_text(grid):
    """Render a grid as a plain-text table with aligned columns.

    Args:
        grid (list[list[tuple]]): display grid.

    Returns:
        str: one line per row, columns separated by " | ".
    """
    texts = grid_texts(grid)
    column_count = max(len(row) for row in texts)
    texts = [row + [""] * (column_count - len(row)) for row in texts]
    widths = [max(len(row[column]) for row in texts) for column in range(column_count)]
    lines = [" | ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip()
             for row in texts]
    return "\n".join(lines)


def grid_to_markdown(grid):
    """Render a grid as a Markdown table (first row is the header).

    Args:
        grid (list[list[tuple]]): display grid.

    Returns:
        str: Markdown table text.
    """
    texts = [[cell.replace("|", "\\|") for cell in row] for row in grid_texts(grid)]
    column_count = max(len(row) for row in texts)
    texts = [row + [""] * (column_count - len(row)) for row in texts]
    lines = ["| " + " | ".join(texts[0]) + " |", "|" + " --- |" * column_count]
    lines += ["| " + " | ".join(row) + " |" for row in texts[1:]]
    return "\n".join(lines)
