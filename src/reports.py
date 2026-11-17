"""Report functions of Tables_Ch10.nb, returning RAW numbers only.

Each function translates one notebook function and returns a pandas
DataFrame of full-precision floats.  Rounding and layout live in
``formatting.py``; nothing here rounds, and nothing here reads ``reference/``.

Notebook function      -> Python function         -> output number(s)
    Out[38] Module     -> holdings_table          -> 1
    displayRF          -> displayRF               -> 2
    reportFunction1    -> reportFunction1         -> 3, 4, 5, 6, 7
    tableContributers  -> tableContributers       -> 4, 5, 6
    bestReplicatePort  -> bestReplicatePort       -> 7
    volbySubPortfolio  -> volbySubPortfolio       -> 8
    varsumm            -> varsumm                 -> 9
"""

import math

import numpy as np
import pandas as pd

import distfn

CURRENCY_SYMBOLS = ["$", "¥", "£", "€"]
CURRENCY_ISOCODES = ["USD", "JPY", "GBP", "EUR"]
RISK_CATEGORIES = ["FI - rates", "FI - swap spreads", "Credit", "Equity",
                   "Commodity", "FX", "Volatility"]
REPLICATING_SIZES = 5       # ``nosec`` in bestReplicatePort
VAR_PROBABILITY = 1 / 255   # "1-out-of-255" trading days
VAR_MIXTURE_ALPHA = 0.01    # varsumm overrides DistFn1.m's alpha = 0.05
VAR_MIXTURE_BETA = 5        # varsumm overrides DistFn1.m's beta = 3


def holdings_table(seclist, holdings, subportfolio, data):
    """Translate the notebook's holdings display (Out[38]) for ALL positions.

    The notebook hard-codes ``n = 9`` rows, so it shows only 9 of 11
    positions; this function returns every position.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        subportfolio (list[str]): subportfolio label of each position.
        data (dict): static data from ``sampleport.load_data()``.

    Returns:
        pandas.DataFrame: one row per position with columns ``Position``
        (1-based position number, the unique identifier), ``Security``,
        ``Amount (mn local)``, ``Curr`` and ``Subportfolio``.
    """
    rows = []
    for position, (security, holding, label) in enumerate(
            zip(seclist, holdings, subportfolio), start=1):
        symbol = distfn.fxsymb(security, CURRENCY_SYMBOLS, CURRENCY_ISOCODES, data)
        rows.append({"Position": position, "Security": security,
                     "Amount (mn local)": holding, "Curr": symbol, "Subportfolio": label})
    return pd.DataFrame(rows)


def displayRF(seclist, holdings, settledate, data):
    """Translate ``displayRF``: Table 1, securities, risk factors and DV01s.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        pandas.DataFrame: one row per (position, risk factor).  Position-level
        columns (``Position``, ``Security``, ``Curr``, ``Notional``,
        ``Security Vol``) repeat on each row; risk-factor columns are ``Risk
        Factor``, ``DV01``, ``DV01 units``, ``RF unit Vol`` and ``RF pos'n
        Vol`` (= |DV01 x unit vol|).
    """
    _, dv01_names, dv01_values = distfn.populateSecDV01s(seclist, holdings, settledate, data)
    _, security_vols = distfn.secVolbyVCV(seclist, holdings, settledate, data)
    rows = []
    for position, security in enumerate(seclist):
        symbol = distfn.fxsymb(security, CURRENCY_SYMBOLS, CURRENCY_ISOCODES, data)
        for riskfactor, dv01 in zip(dv01_names[position], dv01_values[position]):
            factor_index = data["riskFactorNames"].index(riskfactor)
            unit_vol = data["marketVols"][data["marketDataNames"].index(riskfactor)]
            rows.append({
                "Position": position + 1, "Security": security, "Curr": symbol,
                "Notional": holdings[position], "Security Vol": security_vols[position],
                "Risk Factor": riskfactor, "DV01": dv01,
                "DV01 units": data["riskFactorBumpTypes"][factor_index],
                "RF unit Vol": unit_vol, "RF pos'n Vol": abs(dv01 * unit_vol),
            })
    return pd.DataFrame(rows)


def category_summary(portvol, data):
    """Translate the first block of ``reportFunction1``: volatility by risk category.

    Args:
        portvol (dict): result of ``distfn.portVolbyVCVextended``.
        data (dict): static data.

    Returns:
        pandas.DataFrame: rows "Overall" then the seven risk categories;
        columns ``Category``, ``Exp Vol ($)``, ``Contribution`` (percent) and
        ``Correlation``.  Correlation is NaN for "Overall" and for a category
        with zero volatility (Mathematica leaves that cell blank).
    """
    combined_vol = portvol["portvol"]
    categories = [data["riskFactorCategory"][data["riskFactorNames"].index(name)]
                  for name in portvol["rflist"]]
    rows = [{"Category": "Overall", "Exp Vol ($)": combined_vol,
             "Contribution": 100.0, "Correlation": np.nan}]
    for category in RISK_CATEGORIES:
        in_category = np.array([label == category for label in categories])
        category_dv01s = np.where(in_category, portvol["portdv01s"], 0.0)
        category_vol = math.sqrt(category_dv01s @ portvol["vcv"] @ category_dv01s)
        contribution = float(np.sum(portvol["mcp"][in_category]))
        correlation = contribution * combined_vol / category_vol if category_vol > 0 else np.nan
        rows.append({"Category": category, "Exp Vol ($)": category_vol,
                     "Contribution": 100 * contribution, "Correlation": correlation})
    return pd.DataFrame(rows)


def tableContributers(ordering, portvol):
    """Translate ``tableContributers``: one row per selected risk factor.

    Args:
        ordering (sequence[int]): 0-based indexes of the risk factors to show,
            in display order.
        portvol (dict): result of ``distfn.portVolbyVCVextended``.

    Returns:
        pandas.DataFrame: columns ``Risk Factor``, ``Exp Vol (1-sig P&L)``,
        ``Contribution`` (percent), ``Curr Pos'n (mn eqv)``, ``Trade to best
        Hedge (eqv)``, ``% Reduction in Vol to Best Hedge`` and ``% Reduction
        in Vol to Zero Pos'n``.
    """
    combined_vol = portvol["portvol"]
    vol_explained = 100.0 * (1 - portvol["volbesthedge"] / combined_vol)
    rows = []
    for index in ordering:
        rows.append({
            "Risk Factor": portvol["rflist"][index],
            "Exp Vol (1-sig P&L)": portvol["rfvols"][index],
            "Contribution": 100 * portvol["mcp"][index],
            "Curr Pos'n (mn eqv)": portvol["besthedge"][index] + portvol["repport"][index],
            "Trade to best Hedge (eqv)": -portvol["repport"][index],
            "% Reduction in Vol to Best Hedge": vol_explained[index],
            "% Reduction in Vol to Zero Pos'n": 100 * portvol["contallornot"][index] / combined_vol,
        })
    return pd.DataFrame(rows)


def mathematica_ordering(values, count):
    """Translate ``Ordering[list, n]``: positions of the ``count`` smallest values.

    Args:
        values (numpy.ndarray): values to rank.
        count (int): how many positions to return.

    Returns:
        list[int]: 0-based positions of the smallest values; ties keep their
        original order, as Mathematica's ``Ordering`` does.
    """
    return [int(index) for index in np.argsort(values, kind="stable")[:count]]


def best_next_asset(selected, part, sigma, port_variance):
    """Helper for ``bestReplicatePort``: the asset that most reduces variance.

    Translates the inner ``For[j = 1, ...]`` loop.

    Args:
        selected (list[int]): indexes already in the replicating portfolio.
        part (numpy.ndarray): ``sigma . delta``.
        sigma (numpy.ndarray): variance-covariance matrix.
        port_variance (float): variance of the full portfolio.

    Returns:
        tuple[int | None, float]: ``(index of the best asset, residual
        variance with it added)``.  The first asset wins a tie (strict ``<``).
        The index is None if no asset lowers the variance.
    """
    best_index, best_variance = None, port_variance
    for candidate in range(len(part)):
        if candidate in selected:
            continue
        indexes = selected + [candidate]
        hedge = np.linalg.solve(sigma[np.ix_(indexes, indexes)], part[indexes])
        residual_variance = port_variance - part[indexes] @ hedge
        if residual_variance < best_variance:
            best_index, best_variance = candidate, residual_variance
    return best_index, best_variance


def bestReplicatePort(delta, sigma, rfnames, rfunitDV01s):
    """Translate ``bestReplicatePort``: stepwise best replicating portfolios.

    Builds replicating portfolios of 1, 2, ... 5 risk factors.  At each step
    it adds the risk factor that, together with those already chosen, removes
    the most variance; earlier choices are never revisited.

    Args:
        delta (numpy.ndarray): portfolio DV01 by risk factor.
        sigma (numpy.ndarray): variance-covariance matrix of the risk factors.
        rfnames (list[str]): risk-factor names.
        rfunitDV01s (numpy.ndarray): DV01 of 1mn of each equivalent security.

    Returns:
        pandas.DataFrame: one row per portfolio size, with columns ``Assets``
        (the size), ``% Var`` and ``% Vol`` explained, ``Asset 1..5`` (names in
        the order chosen) and ``Eqv Pos'n 1..5`` (mn of equivalent security;
        0 where the risk factor has no equivalent).  Unused cells are None/NaN.
        Stops early if there are fewer than five risk factors or no further
        asset lowers the variance (Mathematica fails in that case).
    """
    part = sigma @ delta
    port_variance = float(delta @ part)
    selected, rows = [], []
    for size in range(1, min(REPLICATING_SIZES, len(delta)) + 1):
        best_index, residual_variance = best_next_asset(selected, part, sigma, port_variance)
        if best_index is None:
            break
        selected = selected + [best_index]
        hedge = np.linalg.solve(sigma[np.ix_(selected, selected)], part[selected])
        positions = distfn.divide_where_nonzero(hedge, rfunitDV01s[selected])
        residual_variance = max(residual_variance, 0.0)
        row = {"Assets": size,
               "% Var": 100 * (1 - residual_variance / port_variance),
               "% Vol": 100 * (1 - math.sqrt(residual_variance) / math.sqrt(port_variance))}
        for slot in range(REPLICATING_SIZES):
            used = slot < size
            row[f"Asset {slot + 1}"] = rfnames[selected[slot]] if used else None
            row[f"Eqv Pos'n {slot + 1}"] = positions[slot] if used else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def reportFunction1(seclist, holdings, settledate, data):
    """Translate ``reportFunction1`` (NAV = 1 version): the five summary reports.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        list[pandas.DataFrame]: five raw tables, in the notebook's order:
        [0] risk-category summary, [1] top three contributors, [2] the single
        most negative contributor ("best single hedge"), [3] the three risk
        factors with the lowest volatility at their best hedge, [4] best
        replicating portfolios.
    """
    portvol = distfn.portVolbyVCVextended(seclist, holdings, settledate, data)
    top_contributors = mathematica_ordering(-portvol["mcp"], 3)
    most_negative = mathematica_ordering(portvol["mcp"], 1)
    best_hedges = mathematica_ordering(portvol["volbesthedge"], 3)
    return [
        category_summary(portvol, data),
        tableContributers(top_contributors, portvol),
        tableContributers(most_negative, portvol),
        tableContributers(best_hedges, portvol),
        bestReplicatePort(portvol["portdv01s"], portvol["vcv"],
                          portvol["rflist"], portvol["unitdv01s"]),
    ]


def mathematica_union(labels):
    """Translate ``Union[list]`` for strings: sorted unique values.

    Args:
        labels (list[str]): labels, possibly repeated.

    Returns:
        list[str]: unique labels in Mathematica's canonical order
        (alphabetical ignoring case; lower case first when otherwise equal).
    """
    return sorted(set(labels), key=lambda label: (label.lower(), label.swapcase()))


def volbySubPortfolio(seclist, holdings, settledate, subportfolio, data):
    """Translate ``volbySubPortfolio``: volatility and contribution by subportfolio.

    Each subportfolio is valued by zeroing the holdings of every other
    position, so all DV01 vectors share the same risk-factor order.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        subportfolio (list[str]): subportfolio label of each position.
        data (dict): static data.

    Returns:
        pandas.DataFrame: rows "Overall" then each subportfolio in sorted
        order; columns ``Subportfolio``, ``Exp Vol ($)``, ``Contribution``
        (percent) and ``Correlation`` (NaN for "Overall" or zero volatility).
    """
    full = distfn.portVolbyVCVextended(seclist, holdings, settledate, data)
    overall_vol = full["portvol"]
    partial = full["vcv"] @ full["portdv01s"]
    rows = [{"Subportfolio": "Overall", "Exp Vol ($)": overall_vol,
             "Contribution": 100.0, "Correlation": np.nan}]
    for label in mathematica_union(subportfolio):
        sub_holdings = [holding if owner == label else 0
                        for holding, owner in zip(holdings, subportfolio)]
        sub = distfn.portVolbyVCVextended(seclist, sub_holdings, settledate, data)
        contribution = 100 * float(sub["portdv01s"] @ partial) / overall_vol ** 2
        sub_vol = sub["portvol"]
        correlation = contribution * overall_vol / (100 * sub_vol) if sub_vol > 0 else np.nan
        rows.append({"Subportfolio": label, "Exp Vol ($)": sub_vol,
                     "Contribution": contribution, "Correlation": correlation})
    return pd.DataFrame(rows)


def varsumm(seclist, holdings, settledate, data):
    """Translate ``varsumm``: volatility and 1-out-of-255 Value-at-Risk.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        pandas.DataFrame: columns ``Measure`` and ``Value`` (USD; VaR values
        are negative).  Rows: volatility, normal VaR, Student-t (6 df) VaR,
        normal-mixture VaR (alpha = 1%, beta = 5) and the 4-sigma rule of thumb.
    """
    vol = distfn.portVolbyVCV(seclist, holdings, settledate, data)
    mixture = distfn.normalmix(vol, VAR_MIXTURE_ALPHA, VAR_MIXTURE_BETA)
    rows = [
        ("Volatility", vol),
        ("VaR Normal", distfn.var(distfn.normal, VAR_PROBABILITY, vol)),
        ("VaR Student-t (6df)", distfn.var(distfn.student, VAR_PROBABILITY, vol)),
        ("VaR Normal Mix (α=1% β=5)", distfn.quantile(mixture, VAR_PROBABILITY)),
        ("VaR 4-sigma rule-of-thumb", -4 * vol),
    ]
    return pd.DataFrame(rows, columns=["Measure", "Value"])
