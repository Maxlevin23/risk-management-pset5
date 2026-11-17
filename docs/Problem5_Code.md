---
title: "Problem 5: Code Listing (Python and Mathematica)"
subtitle: "PPHA 42525 Risk Management, Autumn 2026"
---

The original `SamplePort2.m`, `DistFn1.m` and `Tables_Ch10.nb` are unmodified and are in `mathematica/`; they are not repeated here. `reference/scenario2/SamplePort2_scenario2.m` is a copy of `SamplePort2.m` with two changed values (USDYld10yr .0253 to .0353; GBPFX 1/1.4 to 1/1.6).

| Section | Files |
|---|---|
| Python: inputs and static data | `src/inputs.py`, `src/sampleport.py` |
| Python: translation of DistFn1.m | `src/distfn.py` |
| Python: report functions, formatting and the tables script | `src/reports.py`, `src/formatting.py`, `src/tables_ch10.py` |
| Python: verification | `verify.py` |
| Python: scenario inputs | `scenarios/scenario1.py`, `scenarios/scenario2.py`, `scenarios/scenario3.py` |
| Python: tests | `tests/conftest.py`, `tests/helpers.py`, `tests/test_pv_and_dv01.py`, `tests/test_risk_and_distributions.py`, `tests/test_tables.py`, `tests/run_tests.py` |
| Mathematica: scenario inputs and export script | `reference/original/inputs.m`, `reference/scenario1/inputs.m`, `reference/scenario2/inputs.m`, `reference/scenario3/inputs.m`, `mathematica/RunScenarios.wl` |
| Mathematica: table functions extracted from Tables_Ch10.nb | `mathematica/TableFunctions.wl` |
| Configuration | `requirements.txt` |

# Python: inputs and static data

## src/inputs.py

````python
"""THE ONE PLACE where the portfolio inputs are defined.

Changing anything here changes every one of the nine tables.  A test
scenario is simply another file with the same five names (see
``scenarios/``); run it with ``python src/tables_ch10.py scenarios/scenario1.py``.

These are the values set in Tables_Ch10.nb (``seclist``, ``holdings``,
``subportfolio``) and SamplePort2.m (``settledate``).
"""

# Security of each position.  "10yr UST" appears twice on purpose: positions
# are identified by their place in this list, never by name.
SECLIST = ["10yr UST", "5yr Bond Opt", "10yr UST", "10yr Swap", "10yr UKG",
           "FTE CDS", "CAC Index Futures", "FTE Equity", "GBPCash", "EURCash", "5yr UST"]

# Amount of each position in millions of its own currency (negative = short).
HOLDINGS = [20, -20, 30, -20, 25, 55, 7, 5, -10, 0, 0]

# Subportfolio of each position.
SUBPORTFOLIO = ["Government", "Government", "Swaps", "Swaps", "Government", "Credit",
                "Equity", "Equity", "Government", "Equity", "Government"]

# Settlement (valuation) date as a Mathematica date list.
SETTLEDATE = [2009, 1, 27, 0, 0, 0]

# Market data changes relative to SamplePort2.m, e.g. {"GBPFX": 1 / 1.6}.
# Empty for the original portfolio.
MARKET_DATA_OVERRIDES = {}
````

## src/sampleport.py

````python
"""Static data for the sample portfolio: Python translation of SamplePort2.m.

Every list keeps the Mathematica name and the Mathematica ordering, because
DistFn1.m looks things up by position in these parallel lists.  Nothing in
this module is computed; it is a literal transcription generated directly
from SamplePort2.m (see README, "How sampleport.py was produced").

Use ``load_data()`` to get a fresh, independent copy of all lists in one
dictionary.  Functions in ``distfn.py`` take that dictionary as an argument
instead of reading global variables, so a test scenario can change market
data without touching this file.
"""

import copy

# Securities known to the system (one row per security type, not per position).
secNames = ['5yr UST', '10yr UST', '5yr Bond Opt', '10yr Swap', '5yr UKG', '10yr UKG',
 'CAC Index Futures', 'FTE CDS', '5yr Bund', '10yr Bund', 'FTE Equity', 'GBPCash',
 'EURCash', 'Swap201901', 'SPX Index Futures']

# Instrument type of each security.
secType = ['GovtBond', 'GovtBond', 'BondOption', 'Swap', 'GovtBond', 'GovtBond', 'Futures', 'CDS',
 'GovtBond', 'GovtBond', 'Equity', 'Cash', 'Cash', 'SwapActual', 'Futures']

# Names of the static parameters of each security.
secParmNames = [['Coupon', 'MaturityDate', 'Frequency', 'Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'Currency'],
 ['Expiry', 'StrikeYld', 'UnderTerm', 'UnderFreq', 'Type', 'Currency'],
 ['Coupon', 'Years', 'Frequency', 'Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'Currency'], ['betaIndex', 'Currency'],
 ['Coupon', 'Years', 'Frequency', 'Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'Currency'],
 ['betaIndex', 'betaSpec', 'Currency'], ['Currency'], ['Currency'],
 ['Coupon', 'MaturityDate', 'Frequency', 'FloatReset', 'Currency'],
 ['betaIndex', 'Currency']]

# Values of the static parameters (dates are Mathematica date lists {y,m,d,h,m,s}).
secParmValues = [[3.75, [2013, 11, 15, 0, 0, 0], 2, 'USD'], [3.75, [2018, 11, 15, 0, 0, 0], 2, 'USD'],
 [0.5, 0.0168, 5, 2, 'C', 'USD'], [2.8, 10, 2, 'USD'],
 [5, [2014, 9, 15, 0, 0, 0], 2, 'GBP'], [5, [2018, 3, 15, 0, 0, 0], 2, 'GBP'],
 [1, 'EUR'], [1.5, 5, 2, 'GBP'], [4, [2013, 10, 15, 0, 0, 0], 2, 'EUR'],
 [3.75, [2019, 7, 15, 0, 0, 0], 2, 'EUR'], [0.7, 1, 'EUR'], ['GBP'], ['EUR'],
 [2.8, [2019, 1, 15, 0, 0, 0], 2, 2.3, 'USD'], [1, 'USD']]

# Market data inputs each PV function needs, in the order the PV function expects.
secMktInputNames = [['USDYld5yr', 'USDFX'], ['USDYld10yr', 'USDFX'],
 ['RShort', 'USDYld5yr', 'US5yrOptionVol', 'USDFX'],
 ['USDYld10yr', 'USDSwapSp10yr', 'USDFX'], ['GBPYld5yr', 'GBPFX'],
 ['GBPYld10yr', 'GBPFX'], ['CACEqIndex'], ['GBPYld5yr', 'GBPCredSprd5yr', 'GBPFX'],
 ['EURYld5yr', 'EURFX'], ['EURYld10yr', 'EURFX'],
 ['CACEqIndex', 'FTEEqSpecific', 'EURFX'], ['GBPFX'], ['EURFX'],
 ['USDYld10yr', 'USDSwapSp10yr', 'USDFX'], ['SPXEqIndex']]

# Risk factors each security is exposed to (a subset of its market inputs).
secRiskFactorNames = [['USDYld5yr'], ['USDYld10yr'], ['USDYld5yr', 'US5yrOptionVol'],
 ['USDYld10yr', 'USDSwapSp10yr'], ['GBPYld5yr', 'GBPFX'], ['GBPYld10yr', 'GBPFX'],
 ['CACEqIndex'], ['GBPYld5yr', 'GBPCredSprd5yr', 'GBPFX'], ['EURYld5yr', 'EURFX'],
 ['EURYld10yr', 'EURFX'], ['CACEqIndex', 'FTEEqSpecific', 'EURFX'], ['GBPFX'],
 ['EURFX'], ['USDYld10yr', 'USDSwapSp10yr'], ['SPXEqIndex']]

# Name of the PV function for each security (looked up in distfn.PV_FUNCTIONS).
secPVFunction = ['bondpv', 'bondpv', 'bondoptionpv', 'swappv', 'bondpv', 'bondpv', 'eqtyFutpv',
 'simpCDSpv', 'bondpv', 'bondpv', 'eqtypv', 'cashpv', 'cashpv', 'swappvactual',
 'eqtyFutpv']

# All risk factors, in report order.
riskFactorNames = ['USDYld5yr', 'USDYld10yr', 'US5yrOptionVol', 'USDSwapSp5yr', 'USDSwapSp10yr',
 'SPXEqIndex', 'USDVol', 'GBPYld5yr', 'GBPYld10yr', 'GBPCredSprd5yr', 'GBPEqIndex',
 'GBPFX', 'EURYld5yr', 'EURYld10yr', 'CACEqIndex', 'FTEEqSpecific', 'EURFX']

# Risk category of each risk factor (used by the category summary).
riskFactorCategory = ['FI - rates', 'FI - rates', 'Volatility', 'FI - swap spreads', 'FI - swap spreads',
 'Equity', 'Volatility', 'FI - rates', 'FI - rates', 'Credit', 'Equity', 'FX',
 'FI - rates', 'FI - rates', 'Equity', 'Equity', 'FX']

# 'Equivalent' security used to express each risk factor as a position ('' = none).
riskFactorEqvs = ['5yr UST', '10yr UST', '', '5yr Swap', '10yr Swap', 'SPX Index Futures', '', '5yr UKG',
 '10yr UKG', 'FTE CDS', 'UKX Equity Index', 'GBPCash', '5yr Bund', '10yr Bund',
 'CAC Index Futures', 'FTE Equity', 'EURCash']

# Size of the up/down bump used for numerical DV01s.
riskFactorBumpSize = [0.0005, 0.0005, 0.001, 0.0005, 0.0005, 0.01, 0.0005, 0.001, 0.0005, 0.0005, 0.01, 0.01,
 0.0005, 0.0005, 0.01, 0.01, 0.01]

# 'level' = additive bump, 'percent' = multiplicative bump.
riskFactorBumpTypes = ['level', 'level', 'level', 'level', 'level', 'percent', 'level', 'level', 'level',
 'level', 'percent', 'percent', 'level', 'level', 'percent', 'percent', 'percent']

# Unit and sign convention of the DV01 (yields: per -1bp; FX: per -100%).
riskFactorBumpUnit = [-0.0001, -0.0001, 0.01, -0.0001, -0.0001, 1, 0.01, -0.0001, -0.0001, -0.0001, 1, -1,
 -0.0001, -0.0001, 1, 1, -1]

# Multiplier used only by dv01sec (kept for completeness).
riskFactorMult = [0.01, 0.01, 1, 0.01, 0.01, 1, 1, 0.01, 0.01, 0.01, 1, 1, 0.01, 0.01, 1, 1, 1]

# Names of all market data items.
marketDataNames = ['USDYld5yr', 'USDYld10yr', 'USDSwapSp5yr', 'USDSwapSp10yr', 'SPXEqIndex', 'USDFX',
 'US5yrOptionVol', 'RShort', 'GBPYld5yr', 'GBPYld10yr', 'GBPCredSprd5yr', 'GBPEqIndex',
 'GBPFX', 'EURYld5yr', 'EURYld10yr', 'CACEqIndex', 'FTEEqSpecific', 'EURFX']

# Current values of the market data items (FX is foreign currency per USD).
marketDataValues = [0.0178, 0.0253, 0.006, 0.0027, 1, 1, 0.2, 0.005, 0.0314, 0.0367, 0.0159, 1,
 1 / 1.4, 0.022, 0.0297, 1, 1, 1 / 1.3]

# Correlation matrix of market data items, ordered as marketDataNames.
corrmatrix = [[1, 0.894463548, -0.046442049, 0.215806103, -0.397778621, 0, 0.343256562, 0,
  0.626533382, 0.655431691, -0.059651541, -0.312714946, 0.121469905, 0.65948846,
  0.71256132, -0.26649492, 0.129181583, -0.034390337],
 [0.894463548, 1, 0.14463409, 0.184982773, -0.320444678, 0, 0.265668751, 0, 0.623585779,
  0.736716907, -0.053400865, -0.275690141, 0.07932111, 0.641136207, 0.793129921,
  -0.240000046, 0.123690934, -0.080855547],
 [-0.046442049, 0.14463409, 1, 0.626543888, 0.246648623, 0, -0.299240428, 0,
  -0.11916476, -0.037710308, 0.004344537, 0.218729622, -0.210396218, -0.057926929,
  -0.047641079, 0.055636246, 0.101272798, -0.160910017],
 [0.215806103, 0.184982773, 0.626543888, 1, -0.104031544, 0, 0.039751003, 0,
  -0.023657403, 0.005908368, 0.104757727, -0.09149073, 0.029682413, 0.072757103,
  0.037720673, -0.1372426, 0.104601481, 0.140121204],
 [-0.397778621, -0.320444678, 0.246648623, -0.104031544, 1, 0, -0.794404549, 0,
  -0.349803599, -0.319338369, -0.131978371, 0.892341131, -0.359591444, -0.411833485,
  -0.391498194, 0.608771915, -0.153404398, -0.345395088],
 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
 [0.343256562, 0.265668751, -0.299240428, 0.039751003, -0.794404549, 0, 1, 0,
  0.226776215, 0.217550865, 0.100327889, -0.778156708, 0.27033281, 0.317698524,
  0.317910894, -0.492969891, 0.131788329, 0.24907896],
 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
 [0.626533382, 0.623585779, -0.11916476, -0.023657403, -0.349803599, 0, 0.226776215, 0,
  1, 0.869867185, -0.195092662, -0.274880434, 0.300188108, 0.724460792, 0.743115694,
  -0.182727578, 0.013357649, 0.066532588],
 [0.655431691, 0.736716907, -0.037710308, 0.005908368, -0.319338369, 0, 0.217550865, 0,
  0.869867185, 1, -0.059075318, -0.283556745, 0.202075747, 0.720488508, 0.831000084,
  -0.190031077, 0.038113338, 0.039683491],
 [-0.059651541, -0.053400865, 0.004344537, 0.104757727, -0.131978371, 0, 0.100327889, 0,
  -0.195092662, -0.059075318, 1, -0.163437316, -0.075315907, 0.011321447, 0.031073451,
  -0.209829821, -0.318983049, 0.112362036],
 [-0.312714946, -0.275690141, 0.218729622, -0.09149073, 0.892341131, 0, -0.778156708, 0,
  -0.274880434, -0.283556745, -0.163437316, 1, -0.326947659, -0.343931629, -0.347042167,
  0.669830912, -0.181410241, -0.313681699],
 [0.121469905, 0.07932111, -0.210396218, 0.029682413, -0.359591444, 0, 0.27033281, 0,
  0.300188108, 0.202075747, -0.075315907, -0.326947659, 1, 0.281368999, 0.204330148,
  -0.259235668, 0.095974521, 0.58828034],
 [0.65948846, 0.641136207, -0.057926929, 0.072757103, -0.411833485, 0, 0.317698524, 0,
  0.724460792, 0.720488508, 0.011321447, -0.343931629, 0.281368999, 1, 0.869155366,
  -0.267960434, 0.11248309, 0.283408807],
 [0.71256132, 0.793129921, -0.047641079, 0.037720673, -0.391498194, 0, 0.317910894, 0,
  0.743115694, 0.831000084, 0.031073451, -0.347042167, 0.204330148, 0.869155366, 1,
  -0.283584095, 0.101671827, 0.173593297],
 [-0.26649492, -0.240000046, 0.055636246, -0.1372426, 0.608771915, 0, -0.492969891, 0,
  -0.182727578, -0.190031077, -0.209829821, 0.669830912, -0.259235668, -0.267960434,
  -0.283584095, 1, -0.517062776, -0.269158342],
 [0.129181583, 0.123690934, 0.101272798, 0.104601481, -0.153404398, 0, 0.131788329, 0,
  0.013357649, 0.038113338, -0.318983049, -0.181410241, 0.095974521, 0.11248309,
  0.101671827, -0.517062776, 1, 0.141113112],
 [-0.034390337, -0.080855547, -0.160910017, 0.140121204, -0.345395088, 0, 0.24907896, 0,
  0.066532588, 0.039683491, 0.112362036, -0.313681699, 0.58828034, 0.283408807,
  0.173593297, -0.269158342, 0.141113112, 1]]

# Daily volatility of each market data item (bp/day for yields, fraction/day otherwise).
marketVols = [7.073478043, 7.148000008, 2.535396254, 2.235124477, 0.015460348, 0, 2.040043844, 0,
 6.916175288, 6.569751878, 1.925656495, 0.015451441, 0.008110121, 6.141800667,
 5.734588953, 0.025365051, 0.028395161, 0.007908532]

# Default settlement date from SamplePort2.m.
settledate = [2009, 1, 27, 0, 0, 0]

DATA_KEYS = (
    "secNames", "secType", "secParmNames", "secParmValues", "secMktInputNames",
    "secRiskFactorNames", "secPVFunction", "riskFactorNames", "riskFactorCategory",
    "riskFactorEqvs", "riskFactorBumpSize", "riskFactorBumpTypes", "riskFactorBumpUnit",
    "riskFactorMult", "marketDataNames", "marketDataValues", "corrmatrix", "marketVols",
    "settledate",
)


def load_data(market_data_overrides=None, market_vol_overrides=None):
    """Return an independent copy of every SamplePort2.m list in one dictionary.

    Args:
        market_data_overrides (dict[str, float] | None): market data values to
            replace, keyed by name in ``marketDataNames`` (e.g. ``{"GBPFX": 1/1.6}``).
            This is how a market-data test scenario is expressed.
        market_vol_overrides (dict[str, float] | None): daily volatilities to
            replace, keyed the same way.

    Returns:
        dict: keys are the Mathematica list names in ``DATA_KEYS``; values are
        deep copies, so changing them never changes this module.

    Raises:
        KeyError: if an override names something not in ``marketDataNames``.
    """
    module_globals = globals()
    data = {key: copy.deepcopy(module_globals[key]) for key in DATA_KEYS}
    for target_key, overrides in (("marketDataValues", market_data_overrides),
                                  ("marketVols", market_vol_overrides)):
        for name, value in (overrides or {}).items():
            if name not in data["marketDataNames"]:
                raise KeyError(f"{name!r} is not in marketDataNames")
            data[target_key][data["marketDataNames"].index(name)] = value
    return data
````

# Python: translation of DistFn1.m

## src/distfn.py

````python
"""Python translation of DistFn1.m (valuation, DV01, portfolio risk, distributions).

Each function names the Mathematica function it translates in its docstring.
The Mathematica code reads global lists (secNames, marketDataValues, ...);
here every function receives those lists in the ``data`` dictionary returned
by ``sampleport.load_data()``, so nothing depends on module-level state.

Sections, in the same order as DistFn1.m:
    1. Dates and the annuity formula
    2. Instrument PV functions
    3. Look-ups and position PV
    4. DV01s (bump and revalue)
    5. Variance-covariance, volatility, contributions, best hedges
    6. Distribution functions (normal, Student-t, two-point normal mixture)

Only numpy and the standard library are used.
"""

import calendar
import datetime
import math
from fractions import Fraction
from statistics import NormalDist

import numpy as np

# ---------------------------------------------------------------------------
# 1. Dates and the annuity formula
# ---------------------------------------------------------------------------


def serialday(date):
    """Translate ``serialday``: serial day number of a Mathematica date list.

    Args:
        date (sequence[int]): ``[year, month, day, ...]``; only the first three
            entries are used (the Mathematica dates all have time 0:00:00).

    Returns:
        int: days since 1900-01-01, plus 2 (the Mathematica/Excel convention).
        Only differences of serial days are ever used.
    """
    year, month, day = date[0], date[1], date[2]
    return (datetime.date(year, month, day) - datetime.date(1900, 1, 1)).days + 2


def date_plus_months(date, months):
    """Translate ``DatePlus[date, {n, "Month"}]``: shift a date by whole months.

    Args:
        date (sequence[int]): ``[year, month, day, ...]``.
        months (int): number of months to add (may be negative).

    Returns:
        list[int]: ``[year, month, day]``; a day past the end of the target
        month is clamped to the last day of that month, as Mathematica does.
    """
    month_index = date[0] * 12 + (date[1] - 1) + months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(date[2], calendar.monthrange(year, month)[1])
    return [year, month, day]


def pv(rate, nper, pmt, fv):
    """Translate ``pv``: present value of a level annuity plus a final amount.

    Args:
        rate (float): periodic discount rate (decimal).
        nper (int): number of periods.
        pmt (float): payment per period.
        fv (float): amount paid at the end.

    Returns:
        float: ``pmt * (1 - (1+rate)^-nper) / rate + fv * (1+rate)^-nper``.
    """
    discount = 1.0 / ((1.0 + rate) ** nper)
    return pmt * (1.0 - discount) / rate + fv * discount


# ---------------------------------------------------------------------------
# 2. Instrument PV functions
#    Common signature: (inputs, settledate, holding, parms, data) -> USD value.
#    ``inputs`` are the market values named in secMktInputNames, in that order.
#    ``holding`` is in millions of local currency.  FX inputs are foreign
#    currency per USD, so dividing by them converts to USD.
# ---------------------------------------------------------------------------


def coupon_dates_around(settledate, maturity_date, frequency):
    """Helper for ``bondprc``: serial days of the coupon dates around settlement.

    Translates the ``d0..d4`` / ``Which[...]`` block of ``bondprc``.

    Args:
        settledate (sequence[int]): settlement date list.
        maturity_date (sequence[int]): maturity date list.
        frequency (int): coupons per year (1 or 2).

    Returns:
        tuple[int, int]: ``(dbefore, dafter)`` with dbefore < settle <= dafter.

    Raises:
        ValueError: if settlement is not inside any of the four candidate
            periods (Mathematica would silently leave the variables undefined).
    """
    months_per_period = 12 if frequency == 1 else 6
    anchor = [settledate[0], maturity_date[1], maturity_date[2]]
    offsets = (-12, -months_per_period, 0, months_per_period, 12)
    candidates = [serialday(date_plus_months(anchor, offset)) for offset in offsets]
    settle_serial = serialday(settledate)
    for date_before, date_after in zip(candidates[:-1], candidates[1:]):
        if date_before < settle_serial <= date_after:
            return date_before, date_after
    raise ValueError("bondprc: settlement date is not in any coupon period")


def bondprc(yld, settledate, parms):
    """Translate ``bondprc``: clean price, accrued interest and dirty price.

    Args:
        yld (float): yield to maturity (decimal, compounded ``frequency`` times a year).
        settledate (sequence[int]): settlement date list.
        parms (list): ``[Coupon %, MaturityDate, Frequency, Currency]`` for a
            bond, or ``[Coupon %, MaturityDate, Frequency, FloatReset %, Currency]``
            for an actual swap (five parameters means "swap", as in Mathematica).

    Returns:
        tuple[float, float, float]: ``(clean price, accrued interest, dirty
        price)`` per 100 notional.
    """
    coupon, maturity_date, frequency = parms[0], parms[1], parms[2]
    yield_per_period = yld / frequency
    date_before, date_after = coupon_dates_around(settledate, maturity_date, frequency)
    settle_serial = serialday(settledate)
    day_fraction = (date_after - settle_serial) / (date_after - date_before)
    # Mathematica divides exact integers and Round[] rounds halves to even.
    periods_after = round(Fraction(serialday(maturity_date) - date_after) * frequency / 365)
    payment = coupon / frequency
    dirty_price = pv(yield_per_period, periods_after, payment, 100.0)
    dirty_price = (payment + dirty_price) / ((1.0 + yield_per_period) ** day_fraction)
    if len(parms) == 5:
        float_reset = parms[3] / frequency
        dirty_price -= (float_reset + 100.0) / ((1.0 + yield_per_period) ** day_fraction)
    accrued_interest = payment * (1.0 - day_fraction)
    return dirty_price - accrued_interest, accrued_interest, dirty_price


def bondpv(inputs, settledate, holding, parms, data):
    """Translate ``bondpv``: USD value of a government bond position.

    Args:
        inputs (list[float]): ``[yield, FX rate]``.
        settledate (sequence[int]): settlement date list.
        holding (float): notional in millions of local currency.
        parms (list): bond parameters (see ``bondprc``).
        data (dict): static data (unused; kept for the common signature).

    Returns:
        float: dirty price x notional, converted to USD.
    """
    return bondprc(inputs[0], settledate, parms)[2] * holding * 10000 / inputs[1]


def swappvactual(inputs, settledate, holding, parms, data):
    """Translate ``swappvactual``: USD value of a swap with a real maturity date.

    Args:
        inputs (list[float]): ``[yield, swap spread, FX rate]``.
        settledate (sequence[int]): settlement date list.
        holding (float): notional in millions (positive = receive fixed).
        parms (list): ``[Coupon, MaturityDate, Frequency, FloatReset, Currency]``.
        data (dict): static data (unused).

    Returns:
        float: fixed leg minus floating leg, in USD.
    """
    swap_rate = inputs[0] + inputs[1]
    return bondprc(swap_rate, settledate, parms)[2] * holding * 10000 / inputs[2]


def swappv(inputs, settledate, holding, parms, data):
    """Translate ``swappv``: USD value of a par-style swap with whole years to run.

    Args:
        inputs (list[float]): ``[yield, swap spread, FX rate]``.
        settledate (sequence[int]): not used (the swap has a term, not a date).
        holding (float): notional in millions (positive = receive fixed).
        parms (list): ``[Coupon %, Years, Frequency, Currency]``.
        data (dict): static data (unused).

    Returns:
        float: (fixed-leg PV - 100) x notional, in USD.
    """
    coupon, years, frequency = parms[0], parms[1], parms[2]
    yield_per_period = (inputs[0] + inputs[1]) / frequency
    price = pv(yield_per_period, years * frequency, coupon / frequency, 100.0)
    return (price - 100.0) * holding * 10000 / inputs[2]


def bondoptionprc(expiry, rshort, fyld, strike, vol, underlier_term, underlier_freq, putcall):
    """Translate ``bondoptionprc``: Black price of an option on a bond yield.

    Args:
        expiry (float): time to expiry in years.
        rshort (float): short rate used to discount to today.
        fyld (float): forward yield of the underlier.
        strike (float): strike yield.
        vol (float): lognormal yield volatility.
        underlier_term (float): term of the underlying bond in years.
        underlier_freq (int): coupon frequency of the underlying bond.
        putcall (str): ``"P"`` for a put on the bond (payer); anything else is
            priced as a call on the bond (receiver), exactly as in Mathematica.

    Returns:
        float: option price per 100 notional.
    """
    annuity = pv(fyld / underlier_freq, underlier_freq * underlier_term, 1.0 / underlier_freq, 0.0)
    annuity = annuity / ((1.0 + rshort / underlier_freq) ** (underlier_freq * expiry))
    d1 = (math.log(fyld / strike) + (expiry * vol ** 2) / 2.0) / (vol * math.sqrt(expiry))
    d2 = d1 - vol * math.sqrt(expiry)
    p1 = NormalDist().cdf(d1)
    p2 = NormalDist().cdf(d2)
    if putcall == "P":
        return annuity * (fyld * p1 - strike * p2) * 100.0
    return annuity * (fyld * (p1 - 1.0) - strike * (p2 - 1.0)) * 100.0


def bondoptionpv(inputs, settledate, holding, parms, data):
    """Translate ``bondoptionpv``: USD value of a bond option position.

    Args:
        inputs (list[float]): ``[short rate, forward yield, option vol, FX rate]``.
        settledate (sequence[int]): not used.
        holding (float): notional in millions.
        parms (list): ``[Expiry, StrikeYld, UnderTerm, UnderFreq, Type, Currency]``.
        data (dict): static data (unused).

    Returns:
        float: option value in USD.
    """
    price = bondoptionprc(parms[0], inputs[0], inputs[1], parms[1], inputs[2],
                          parms[2], parms[3], parms[4])
    return price * holding * 10000 / inputs[3]


def simpCDSpv(inputs, settledate, holding, parms, data):
    """Translate ``simpCDSpv``: USD value of a simplified credit default swap.

    The CDS is modelled as a risky par bond paying (CDS coupon + risk-free
    yield), discounted at (risk-free yield + credit spread), minus 100.

    Args:
        inputs (list[float]): ``[risk-free yield, credit spread, FX rate]``.
        settledate (sequence[int]): not used.
        holding (float): notional in millions (positive = sold protection).
        parms (list): ``[Coupon %, Years, Frequency, Currency]``.
        data (dict): static data (unused).

    Returns:
        float: CDS value in USD.
    """
    coupon, years, frequency = parms[0], parms[1], parms[2]
    yield_per_period = (inputs[0] + inputs[1]) / frequency
    payment = (coupon + 100.0 * inputs[0]) / frequency
    price = pv(yield_per_period, years * frequency, payment, 100.0)
    return (price - 100.0) * holding * 10000 / inputs[2]


def cashpv(inputs, settledate, holding, parms, data):
    """Translate ``cashpv``: USD value of a foreign-currency cash position.

    Args:
        inputs (list[float]): ``[FX rate]``.
        settledate (sequence[int]): not used.
        holding (float): amount in millions of local currency.
        parms (list): ``[Currency]`` (unused).
        data (dict): static data (unused).

    Returns:
        float: ``holding * 1,000,000 / FX``.
    """
    return holding * 1000000 / inputs[0]


def eqtypv(inputs, settledate, holding, parms, data):
    """Translate ``eqtypv``: USD value of a single-stock position.

    Args:
        inputs (list[float]): ``[index level, specific level, FX rate]``.
        settledate (sequence[int]): not used.
        holding (float): amount in millions of local currency.
        parms (list): ``[betaIndex, betaSpec, Currency]``.
        data (dict): static data (unused).

    Returns:
        float: ``holding * 1e6 * index^betaIndex * specific^betaSpec / FX``.

    Raises:
        ValueError: if there are more inputs than parameters (Mathematica
            returns the string "Error in eqtypv").
    """
    parameter_count = len(parms)
    if parameter_count < len(inputs):
        raise ValueError("Error in eqtypv")
    factor = 1.0
    for level, beta in zip(inputs[:parameter_count - 1], parms[:parameter_count - 1]):
        factor *= level ** beta
    # Mathematica evaluates a*b*c/d as (exact a*b) * (c * d^-1); the same order is
    # used here so results agree to the last bit (it decides "6x10^6" vs "7x10^6").
    return (holding * 1000000) * (factor * (1 / inputs[-1]))


def eqtyFutpv(inputs, settledate, holding, parms, data):
    """Translate ``eqtyFutpv``: USD value (exposure) of an equity index future.

    QUIRK kept from Mathematica: the FX rate is read from the *global, unbumped*
    market data, not from ``inputs``.  A future therefore never shows FX risk,
    and its FX conversion ignores any bumped market data.

    Args:
        inputs (list[float]): ``[index level]``.
        settledate (sequence[int]): not used.
        holding (float): amount in millions of local currency.
        parms (list): ``[betaIndex, Currency]``.
        data (dict): static data; ``marketDataValues`` supplies the FX rate.

    Returns:
        float: ``holding * 1e6 * index^beta / FX``.

    Raises:
        ValueError: if there are more inputs than parameters.
    """
    parameter_count = len(parms)
    if parameter_count < len(inputs):
        raise ValueError("Error in eqtyFutpv")
    factor = 1.0
    for level, beta in zip(inputs[:parameter_count - 1], parms[:parameter_count - 1]):
        factor *= level ** beta
    fx_rate = data["marketDataValues"][data["marketDataNames"].index(parms[1] + "FX")]
    return (holding * 1000000) * (factor * (1 / fx_rate))  # same order as eqtypv


# secPVFunction holds Mathematica symbols; here it holds names looked up below.
PV_FUNCTIONS = {
    "bondpv": bondpv,
    "swappv": swappv,
    "swappvactual": swappvactual,
    "bondoptionpv": bondoptionpv,
    "simpCDSpv": simpCDSpv,
    "cashpv": cashpv,
    "eqtypv": eqtypv,
    "eqtyFutpv": eqtyFutpv,
}

# ---------------------------------------------------------------------------
# 3. Look-ups and position PV
# ---------------------------------------------------------------------------


def pickSecRFfn(security, data):
    """Translate ``pickSecRFfn``: risk-factor names of one security.

    Args:
        security (str): a name in ``secNames``.
        data (dict): static data.

    Returns:
        list[str]: a copy of that security's entry in ``secRiskFactorNames``.
    """
    return list(data["secRiskFactorNames"][data["secNames"].index(security)])


def fxrateSec(security, data):
    """Translate ``fxrateSec``: currency code and FX rate of one security.

    Args:
        security (str): a name in ``secNames``.
        data (dict): static data.

    Returns:
        tuple[str, float]: ``(ISO currency code, FX rate per USD)``.
    """
    security_index = data["secNames"].index(security)
    parameter_names = data["secParmNames"][security_index]
    currency = data["secParmValues"][security_index][parameter_names.index("Currency")]
    fx_rate = data["marketDataValues"][data["marketDataNames"].index(currency + "FX")]
    return currency, fx_rate


def fxsymb(security, symbols, isocodes, data):
    """Translate ``fxsymb``: currency symbol of one security.

    Args:
        security (str): a name in ``secNames``.
        symbols (list[str]): currency symbols, e.g. ``["$", "¥", "£", "€"]``.
        isocodes (list[str]): matching ISO codes, e.g. ``["USD", "JPY", ...]``.
        data (dict): static data.

    Returns:
        str: the symbol whose ISO code equals the security's currency.
    """
    currency, _ = fxrateSec(security, data)
    return symbols[isocodes.index(currency)]


def pvposn(security, holding, settledate, market_data_values, data):
    """Translate ``pvposn``: USD present value of one position.

    Args:
        security (str): a name in ``secNames``.
        holding (float): amount in millions of local currency.
        settledate (sequence[int]): settlement date list.
        market_data_values (list[float]): market data to value with (possibly
            bumped), ordered as ``marketDataNames``.
        data (dict): static data.

    Returns:
        float: position value in USD.
    """
    security_index = data["secNames"].index(security)
    parms = data["secParmValues"][security_index]
    inputs = [market_data_values[data["marketDataNames"].index(name)]
              for name in data["secMktInputNames"][security_index]]
    pv_function = PV_FUNCTIONS[data["secPVFunction"][security_index]]
    return pv_function(inputs, settledate, holding, parms, data)


def pvPort(seclist, holdings, settledate, market_data_values, data):
    """Translate ``pvPort``: USD present value of every position.

    Args:
        seclist (list[str]): security name of each position (duplicates allowed).
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        market_data_values (list[float]): market data to value with.
        data (dict): static data.

    Returns:
        list[float]: one USD value per position, in position order.
    """
    return [pvposn(security, holding, settledate, market_data_values, data)
            for security, holding in zip(seclist, holdings)]


# ---------------------------------------------------------------------------
# 4. DV01s (bump and revalue)
# ---------------------------------------------------------------------------


def bump_market_data(riskfactor, data):
    """Helper for ``populateSecDV01s``: market data bumped up and down.

    Translates the ``Switch[leveltst, "level", ..., "percent", ...]`` block.
    The ``"levelcurveinp"`` branch is not translated: no risk factor in
    SamplePort2.m uses it and it needs ``bootstrapcurve``, which DistFn1.m
    does not define.

    Args:
        riskfactor (str): a name in ``riskFactorNames``.
        data (dict): static data.

    Returns:
        tuple[list[float], list[float], float]: ``(market data up, market data
        down, total bump width h)``.

    Raises:
        ValueError: for a bump type other than "level" or "percent".
    """
    market_index = data["marketDataNames"].index(riskfactor)
    factor_index = data["riskFactorNames"].index(riskfactor)
    base_value = data["marketDataValues"][market_index]
    bump_size = data["riskFactorBumpSize"][factor_index]
    bump_type = data["riskFactorBumpTypes"][factor_index]
    if bump_type == "level":
        value_up, value_down, width = base_value + bump_size, base_value - bump_size, 2 * bump_size
    elif bump_type == "percent":
        value_up, value_down = base_value * (1 + bump_size), base_value / (1 + bump_size)
        width = (1 + bump_size) - (1 / (1 + bump_size))
    else:
        raise ValueError(f"error in populateSecDV01s: bump type {bump_type!r}")
    market_up, market_down = list(data["marketDataValues"]), list(data["marketDataValues"])
    market_up[market_index], market_down[market_index] = value_up, value_down
    return market_up, market_down, width


def populateSecDV01s(seclist, holdings, settledate, data):
    """Translate ``populateSecDV01s``: DV01 of every position to each of its risk factors.

    Positions are identified by their place in ``seclist`` (never by name), so
    a security that appears twice keeps two separate rows.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        tuple[list[str], list[list[str]], list[list[float]]]:
        ``(seclist, risk-factor names per position, DV01s per position)``.
        A DV01 is ``bumpunit * (PV_up - PV_down) / h`` in USD: per 1bp fall in
        a yield or spread, per 1 vol point, per 100% rise in an equity level,
        per 100% fall in an FX rate.

    Raises:
        ValueError: if ``seclist`` is empty.
    """
    if len(seclist) == 0:
        raise ValueError("Error in populateSecDV01s - seclist or rflist empty")
    dv01_names = [pickSecRFfn(security, data) for security in seclist]
    dv01_values = [[0.0] * len(names) for names in dv01_names]
    unique_factors = sorted({name for names in dv01_names for name in names})
    for riskfactor in unique_factors:
        market_up, market_down, width = bump_market_data(riskfactor, data)
        bump_unit = data["riskFactorBumpUnit"][data["riskFactorNames"].index(riskfactor)]
        for position, (security, holding) in enumerate(zip(seclist, holdings)):
            if riskfactor not in dv01_names[position]:
                continue
            factor_position = dv01_names[position].index(riskfactor)
            value_up = pvposn(security, holding, settledate, market_up, data)
            value_down = pvposn(security, holding, settledate, market_down, data)
            dv01_values[position][factor_position] = bump_unit * (value_up - value_down) / width
    return list(seclist), dv01_names, dv01_values


def populatePortDV01s(seclist, holdings, settledate, data):
    """Translate ``populatePortDV01s``: portfolio DV01 to each risk factor.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        tuple[list[str], numpy.ndarray]: ``(risk-factor names, summed DV01s)``.
        Names are in ``riskFactorNames`` order and include every risk factor
        of every listed security, even when the holding (and DV01) is zero.
    """
    _, dv01_names, dv01_values = populateSecDV01s(seclist, holdings, settledate, data)
    totals = dict.fromkeys(data["riskFactorNames"], 0.0)
    has_entry = set()
    for names, values in zip(dv01_names, dv01_values):
        for riskfactor, value in zip(names, values):
            totals[riskfactor] += value
            has_entry.add(riskfactor)
    port_names = [name for name in data["riskFactorNames"] if name in has_entry]
    return port_names, np.array([totals[name] for name in port_names], dtype=float)


def populateEqvDV01s(seclist, settledate, data):
    """Translate ``populateEqvDV01s``: DV01 of one unit of each "equivalent" security.

    Each risk factor has an equivalent security in ``riskFactorEqvs`` (e.g.
    GBPYld10yr -> "10yr UKG").  The result converts a risk-factor DV01 into
    "millions of the equivalent security".

    Args:
        seclist (list[str]): security name of each position.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        tuple[list[str], numpy.ndarray]: ``(risk-factor names, DV01 of 1mn of
        the equivalent security to that same risk factor)``.  The DV01 is 0
        for a risk factor with no equivalent.  Names cover every risk factor
        of the equivalent securities, in ``riskFactorNames`` order.
    """
    factor_names = data["riskFactorNames"]
    portfolio_factors = sorted({name for security in seclist
                                for name in pickSecRFfn(security, data)})
    equivalents = [data["riskFactorEqvs"][factor_names.index(name)] for name in portfolio_factors]
    full_seclist = [security for security in equivalents if security != ""]
    unit_holdings = [1] * len(full_seclist)
    _, dv01_names, dv01_values = populateSecDV01s(full_seclist, unit_holdings, settledate, data)
    unit_dv01 = dict.fromkeys(factor_names, 0.0)
    has_entry = set()
    for security, names, values in zip(full_seclist, dv01_names, dv01_values):
        for riskfactor, value in zip(names, values):
            if data["riskFactorEqvs"][factor_names.index(riskfactor)] == security:
                unit_dv01[riskfactor] = value
            has_entry.add(riskfactor)
    eqv_names = [name for name in factor_names if name in has_entry]
    return eqv_names, np.array([unit_dv01[name] for name in eqv_names], dtype=float)


# ---------------------------------------------------------------------------
# 5. Variance-covariance, volatility, contributions, best hedges
# ---------------------------------------------------------------------------


def populateVCV(rflist, data):
    """Translate ``populateVCV``: variance-covariance matrix of a list of risk factors.

    Correlations are stored for market *levels*; DV01s for yields and FX are
    per *down* move.  Each correlation is therefore multiplied by the product
    of the signs of the two bump units.

    Args:
        rflist (list[str]): risk-factor names (rows and columns of the result).
        data (dict): static data.

    Returns:
        numpy.ndarray: square matrix ``vol_i * vol_j * corr_ij * sign_i * sign_j``.
    """
    market_positions = [data["marketDataNames"].index(name) for name in rflist]
    factor_positions = [data["riskFactorNames"].index(name) for name in rflist]
    vols = np.array([data["marketVols"][k] for k in market_positions], dtype=float)
    signs = np.sign([data["riskFactorBumpUnit"][m] for m in factor_positions])
    correlation = np.array(data["corrmatrix"], dtype=float)[np.ix_(market_positions,
                                                                   market_positions)]
    return np.outer(vols, vols) * correlation * np.outer(signs, signs)


def secVolbyVCV(seclist, holdings, settledate, data):
    """Translate ``secVolbyVCV``: stand-alone daily volatility of each position.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        tuple[list[str], list[float]]: ``(seclist, USD volatility per position)``.
    """
    _, dv01_names, dv01_values = populateSecDV01s(seclist, holdings, settledate, data)
    security_vols = []
    for names, values in zip(dv01_names, dv01_values):
        dv01_vector = np.array(values, dtype=float)
        variance = dv01_vector @ populateVCV(names, data) @ dv01_vector
        security_vols.append(float(np.sqrt(variance)))
    return list(seclist), security_vols


def rfVolbyVCV(seclist, holdings, settledate, data):
    """Translate ``rfVolbyVCV``: stand-alone volatility of each portfolio risk factor.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        tuple[list[str], numpy.ndarray]: ``(risk-factor names, |DV01| x vol)``.
    """
    port_names, port_dv01s = populatePortDV01s(seclist, holdings, settledate, data)
    variances = np.diagonal(populateVCV(port_names, data))
    return port_names, np.sqrt(port_dv01s * port_dv01s * variances)


def portVolbyVCV(seclist, holdings, settledate, data):
    """Translate ``portVolbyVCV``: daily USD volatility of the whole portfolio.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        float: ``sqrt(d' V d)`` where d is the portfolio DV01 vector.
    """
    port_names, port_dv01s = populatePortDV01s(seclist, holdings, settledate, data)
    return float(np.sqrt(port_dv01s @ populateVCV(port_names, data) @ port_dv01s))


def align_unit_dv01s(port_names, eqv_names, eqv_dv01s):
    """Helper for ``portVolbyVCVextended``: unit DV01s in portfolio risk-factor order.

    Translates the ``indexes`` / ``portDV01s1`` block.  Mathematica places the
    values by position; here they are placed by name, which gives the same
    answer whenever every equivalent-security risk factor is also a portfolio
    risk factor (true for every security in SamplePort2.m).

    Args:
        port_names (list[str]): portfolio risk-factor names.
        eqv_names (list[str]): names returned by ``populateEqvDV01s``.
        eqv_dv01s (numpy.ndarray): values returned by ``populateEqvDV01s``.

    Returns:
        numpy.ndarray: unit DV01 per portfolio risk factor (0 where none).
    """
    unit_by_name = dict(zip(eqv_names, eqv_dv01s))
    return np.array([unit_by_name.get(name, 0.0) for name in port_names], dtype=float)


def divide_where_nonzero(numerator, denominator):
    """Helper: element-wise ``numerator / denominator``, 0 where denominator is 0.

    Translates ``Table[If[x != 0, a / x, 0], ...]``.

    Args:
        numerator (numpy.ndarray): values to divide.
        denominator (numpy.ndarray): divisors, same length.

    Returns:
        numpy.ndarray: the quotients, with 0 where the divisor is exactly 0.
    """
    result = np.zeros_like(numerator, dtype=float)
    nonzero = denominator != 0
    result[nonzero] = numerator[nonzero] / denominator[nonzero]
    return result


def portVolbyVCVextended(seclist, holdings, settledate, data):
    """Translate ``portVolbyVCVextended``: volatility, contributions and best hedges.

    Mathematica returns a 13-element list; here the same 13 items are returned
    in a dictionary.  The number in brackets is the Mathematica list position.

    Args:
        seclist (list[str]): security name of each position.
        holdings (list[float]): amount of each position, millions local.
        settledate (sequence[int]): settlement date list.
        data (dict): static data.

    Returns:
        dict: ``portvol`` [1] portfolio volatility; ``mcl`` [2] marginal
        contribution in USD; ``mcp`` [3] marginal contribution as a fraction;
        ``contallornot`` [4] fall in volatility if the risk factor is zeroed;
        ``besthedge`` [5] best-hedge position, mn of equivalent security;
        ``volbesthedge`` [6] volatility at the best hedge; ``rfvols`` [7]
        stand-alone risk-factor volatilities; ``rflist`` [8] names;
        ``unitdv01s`` [9] DV01 of 1mn of the equivalent security; ``corr``
        [10] correlation with the portfolio; ``repport`` [11] replicating
        position, mn eqv; ``portdv01s`` [12] portfolio DV01s; ``vcv`` [13].
    """
    rflist, dv01s = populatePortDV01s(seclist, holdings, settledate, data)
    eqv_names, eqv_dv01s = populateEqvDV01s(seclist, settledate, data)
    unit_dv01s = align_unit_dv01s(rflist, eqv_names, eqv_dv01s)
    vcv = populateVCV(rflist, data)
    covariance = vcv @ dv01s
    variance = float(dv01s @ covariance)
    portvol = math.sqrt(variance)
    intermediate = dv01s * covariance
    diagonal = np.diagonal(vcv)
    variance_by_factor = dv01s * dv01s * diagonal
    # A tiny negative from rounding would be a NaN; Mathematica gives ~0.
    zeroed_variance = np.maximum(variance - 2 * intermediate + variance_by_factor, 0.0)
    hedged_variance = np.maximum(variance - covariance * covariance / diagonal, 0.0)
    return {
        "portvol": portvol,
        "mcl": intermediate / portvol,
        "mcp": intermediate / portvol / portvol,
        "contallornot": portvol - np.sqrt(zeroed_variance),
        "besthedge": divide_where_nonzero(dv01s - covariance / diagonal, unit_dv01s),
        "volbesthedge": np.sqrt(hedged_variance),
        "rfvols": np.sqrt(variance_by_factor),
        "rflist": rflist,
        "unitdv01s": unit_dv01s,
        "corr": covariance / (portvol * np.sqrt(diagonal)),
        "repport": divide_where_nonzero(covariance / diagonal, unit_dv01s),
        "portdv01s": dv01s,
        "vcv": vcv,
    }


# ---------------------------------------------------------------------------
# 6. Distribution functions
#    Mathematica's built-in distributions do not cover the two-point mixture
#    of normals, so DistFn1.m defines pdf / cdf / quantile itself.  A
#    distribution is described here by a small tuple:
#        ("normal", sigma)
#        ("student", sigma, dof)                  sigma = standard deviation
#        ("normalmixture", sigma, alpha, beta)    sigma = standard deviation
#    In the mixture, with probability (1 - alpha) the draw is N(0, s) and with
#    probability alpha it is N(0, beta * s), where
#    s = sigma / sqrt(1 - alpha + alpha * beta^2) so the overall SD is sigma.
# ---------------------------------------------------------------------------

STUDENT_DOF = 6          # ``studentdof`` in DistFn1.m
MIXTURE_ALPHA = 0.05     # ``alpha`` in DistFn1.m (the notebook's varsumm uses 0.01)
MIXTURE_BETA = 3         # ``beta`` in DistFn1.m (the notebook's varsumm uses 5)


def normal(vol):
    """Translate ``normal``: a zero-mean normal distribution with SD ``vol``."""
    return ("normal", vol)


def student(vol, dof=STUDENT_DOF):
    """Translate ``student``: a zero-mean Student-t rescaled to have SD ``vol``."""
    return ("student", vol, dof)


def normalmix(vol, alpha=MIXTURE_ALPHA, beta=MIXTURE_BETA):
    """Translate ``normalmix``: a two-point normal mixture with overall SD ``vol``."""
    return ("normalmixture", vol, alpha, beta)


def mixture_component_sigma(sigma, alpha, beta):
    """Helper: SD of the low-volatility normal inside the mixture (``normsig``)."""
    return sigma / math.sqrt((1 - alpha) + alpha * beta ** 2)


def log_beta_function(a, b):
    """Helper: natural log of the Beta function B(a, b)."""
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def beta_continued_fraction(a, b, x):
    """Helper: continued fraction for the incomplete beta function (Lentz's method).

    Args:
        a (float): first shape parameter (> 0).
        b (float): second shape parameter (> 0).
        x (float): evaluation point, 0 < x < (a + 1) / (a + b + 2).

    Returns:
        float: value of the continued fraction, converged to about 1e-16.
    """
    tiny = 1e-300
    c_term, d_term = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d_term = 1.0 / (d_term if abs(d_term) > tiny else tiny)
    fraction = d_term
    for m in range(1, 500):
        for numerator in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                          -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d_term = 1.0 + numerator * d_term
            d_term = 1.0 / (d_term if abs(d_term) > tiny else tiny)
            c_term = 1.0 + numerator / c_term
            c_term = c_term if abs(c_term) > tiny else tiny
            fraction *= d_term * c_term
        if abs(d_term * c_term - 1.0) < 1e-16:
            break
    return fraction


def regularized_incomplete_beta(a, b, x):
    """Helper: regularized incomplete beta function I_x(a, b).

    Args:
        a (float): first shape parameter (> 0).
        b (float): second shape parameter (> 0).
        x (float): evaluation point in [0, 1].

    Returns:
        float: I_x(a, b), used for the Student-t CDF.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_front = a * math.log(x) + b * math.log(1.0 - x) - log_beta_function(a, b)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_front) * beta_continued_fraction(a, b, x) / a
    return 1.0 - math.exp(log_front) * beta_continued_fraction(b, a, 1.0 - x) / b


def standard_student_cdf(t_value, dof):
    """Helper: CDF of the standard Student-t distribution with ``dof`` degrees of freedom."""
    tail = 0.5 * regularized_incomplete_beta(dof / 2.0, 0.5, dof / (dof + t_value * t_value))
    return 1.0 - tail if t_value > 0 else tail


def standard_student_pdf(t_value, dof):
    """Helper: PDF of the standard Student-t distribution with ``dof`` degrees of freedom."""
    log_norm = -0.5 * math.log(dof) - log_beta_function(0.5, dof / 2.0)
    return math.exp(log_norm - (dof + 1.0) / 2.0 * math.log1p(t_value * t_value / dof))


def pdf(dist, x):
    """Translate ``pdf``: density of a distribution tuple at ``x``.

    Args:
        dist (tuple): a distribution tuple (see the section comment).
        x (float): evaluation point.

    Returns:
        float: the probability density at ``x``.
    """
    if dist[0] == "normalmixture":
        _, sigma, alpha, beta = dist
        component_sigma = mixture_component_sigma(sigma, alpha, beta)
        return ((1 - alpha) * NormalDist(0.0, component_sigma).pdf(x)
                + alpha * NormalDist(0.0, beta * component_sigma).pdf(x))
    if dist[0] == "student":
        scale = dist[1] * math.sqrt((dist[2] - 2) / dist[2])
        return standard_student_pdf(x / scale, dist[2]) / scale
    return NormalDist(0.0, dist[1]).pdf(x)


def cdf(dist, x):
    """Translate ``cdf``: cumulative probability of a distribution tuple at ``x``.

    Args:
        dist (tuple): a distribution tuple (see the section comment).
        x (float): evaluation point.

    Returns:
        float: P(X <= x).
    """
    if dist[0] == "normalmixture":
        _, sigma, alpha, beta = dist
        component_sigma = mixture_component_sigma(sigma, alpha, beta)
        return ((1 - alpha) * NormalDist(0.0, component_sigma).cdf(x)
                + alpha * NormalDist(0.0, beta * component_sigma).cdf(x))
    if dist[0] == "student":
        scale = dist[1] * math.sqrt((dist[2] - 2) / dist[2])
        return standard_student_cdf(x / scale, dist[2])
    return NormalDist(0.0, dist[1]).cdf(x)


def find_root_newton(dist, p, x_start, sigma):
    """Helper for ``quantile``: solve ``cdf(dist, x) = p`` (Mathematica ``FindRoot``).

    Uses Newton's method from ``x_start`` (as FindRoot does), but keeps a
    bracket around the root and bisects whenever a Newton step leaves it, so
    the answer is reliable to about 1e-13 relative to ``sigma``.

    Args:
        dist (tuple): a distribution tuple.
        p (float): target probability, 0 < p < 1.
        x_start (float): starting guess.
        sigma (float): scale of the distribution, used for tolerances.

    Returns:
        float: x such that ``cdf(dist, x)`` equals p.
    """
    low, high = x_start - sigma, x_start + sigma
    while cdf(dist, low) > p:
        low -= 2 * (high - low)
    while cdf(dist, high) < p:
        high += 2 * (high - low)
    x = min(max(x_start, low), high)
    for _ in range(200):
        error = cdf(dist, x) - p
        low, high = (low, x) if error > 0 else (x, high)
        density = pdf(dist, x)
        x_new = x - error / density if density > 0 else low - 1.0
        if not low < x_new < high:
            x_new = 0.5 * (low + high)
        if abs(x_new - x) <= 1e-13 * sigma:
            return x_new
        x = x_new
    return x


def quantile(dist, p):
    """Translate ``quantile``: inverse CDF of a distribution tuple.

    Args:
        dist (tuple): a distribution tuple (see the section comment).
        p (float): probability, strictly between 0 and 1.

    Returns:
        float: x such that P(X <= x) = p.  For the normal the closed form is
        used; for the Student-t and the mixture the root is found numerically,
        starting (as Mathematica does) from the normal quantile.

    Raises:
        ValueError: if p is not strictly between 0 and 1 (Mathematica returns
            the string "Error").
    """
    if p <= 0 or p >= 1:
        raise ValueError("quantile: probability must be strictly between 0 and 1")
    sigma = dist[1]
    x_start = NormalDist(0.0, sigma).inv_cdf(p)
    if dist[0] == "normal":
        return x_start
    return find_root_newton(dist, p, x_start, sigma)


def var(dist_function, prob, vol):
    """Translate ``var``: Value-at-Risk as a quantile of the P&L distribution.

    Args:
        dist_function (callable): ``normal``, ``student`` or ``normalmix``.
        prob (float): tail probability, e.g. ``1/255``.
        vol (float): P&L volatility (standard deviation) in USD.

    Returns:
        float: the ``prob`` quantile (a negative number for a small ``prob``).
    """
    return quantile(dist_function(vol), prob)
````

# Python: report functions, formatting and the tables script

## src/reports.py

````python
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
````

## src/formatting.py

````python
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
        whole = float(amount).is_integer()
        amount_text = str(int(amount)) if whole else str(amount)
        unit = 1.0 if whole else 10.0 ** -len(amount_text.split(".")[1])
        grid.append([label(row[1]), (amount_text, unit), label(row[3]), label(row[4])])
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
````

## src/tables_ch10.py

````python
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
````

# Python: verification

## verify.py

````python
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
````

# Python: scenario inputs

## scenarios/scenario1.py

````python
"""Scenario 1 (required): portfolio changes only.

What changed relative to src/inputs.py, and which pitfall it exercises:
  * EURCash 0 -> 15 and 5yr UST 0 -> 40   (zero holdings become real positions)
  * 10yr UKG 25 -> -25                    (sign flip: long becomes short)
  * GBPCash moved Government -> Credit    (subportfolio reassignment)
The duplicate "10yr UST" (positions 1 and 3) is kept in two subportfolios.

Mathematica twin: reference/scenario1/inputs.m
"""

SECLIST = ["10yr UST", "5yr Bond Opt", "10yr UST", "10yr Swap", "10yr UKG",
           "FTE CDS", "CAC Index Futures", "FTE Equity", "GBPCash", "EURCash", "5yr UST"]

HOLDINGS = [20, -20, 30, -20, -25, 55, 7, 5, -10, 15, 40]

SUBPORTFOLIO = ["Government", "Government", "Swaps", "Swaps", "Government", "Credit",
                "Equity", "Equity", "Credit", "Equity", "Government"]

SETTLEDATE = [2009, 1, 27, 0, 0, 0]

MARKET_DATA_OVERRIDES = {}
````

## scenarios/scenario2.py

````python
"""Scenario 2 (recommended): market-data change, on the Scenario 1 portfolio.

What changed relative to Scenario 1, and which pitfall it exercises:
  * GBPFX      1/1.4  -> 1/1.6   (FX conversion and the GBPFX risk factor)
  * USDYld10yr 0.0253 -> 0.0353  (bond, swap and DV01 revaluation at a new yield)

Mathematica twin: reference/scenario2/inputs.m and
reference/scenario2/SamplePort2_scenario2.m (a modified copy; the original
SamplePort2.m is unchanged).
"""

SECLIST = ["10yr UST", "5yr Bond Opt", "10yr UST", "10yr Swap", "10yr UKG",
           "FTE CDS", "CAC Index Futures", "FTE Equity", "GBPCash", "EURCash", "5yr UST"]

HOLDINGS = [20, -20, 30, -20, -25, 55, 7, 5, -10, 15, 40]

SUBPORTFOLIO = ["Government", "Government", "Swaps", "Swaps", "Government", "Credit",
                "Equity", "Equity", "Credit", "Equity", "Government"]

SETTLEDATE = [2009, 1, 27, 0, 0, 0]

MARKET_DATA_OVERRIDES = {"GBPFX": 1 / 1.6, "USDYld10yr": 0.0353}
````

## scenarios/scenario3.py

````python
"""Scenario 3 (bonus): different securities, settlement date and fractional sizes.

What changed, and which pitfall it exercises:
  * Settlement date 27-Jan-2009 -> 30-Jun-2009   (day counts, accrued interest,
    number of remaining coupons)
  * Securities not in the original portfolio: 5yr UKG, 5yr Bund, 10yr Bund,
    Swap201901 (dated swap, uses bondprc's 5-parameter branch) and SPX Index
    Futures (USD future)                         (new PV functions, EUR yields)
  * "10yr UST" held +12.5 and -12.5 in two subportfolios: the positions cancel
    in the total but not inside each subportfolio (duplicate securities)
  * Non-integer holdings and a zero holding (GBPCash)
  * New subportfolio names, so the sorted order of the report rows changes

Mathematica twin: reference/scenario3/inputs.m
"""

SECLIST = ["5yr UST", "10yr UST", "10yr UST", "Swap201901", "5yr UKG", "10yr Bund",
           "5yr Bund", "SPX Index Futures", "FTE Equity", "FTE CDS", "EURCash",
           "GBPCash", "5yr Bond Opt"]

HOLDINGS = [35, -12.5, 12.5, -40, 18, -22, 30, -9, 6, 25, -8, 0, 10]

SUBPORTFOLIO = ["Rates", "Rates", "Macro", "Macro", "Rates", "Macro", "Rates",
                "Equity", "Equity", "Credit", "Macro", "Credit", "Rates"]

SETTLEDATE = [2009, 6, 30, 0, 0, 0]

MARKET_DATA_OVERRIDES = {}
````

# Python: tests

## tests/conftest.py

````python
"""Shared test setup: make ``src/`` and the project root importable."""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
for folder in (PROJECT_DIR, PROJECT_DIR / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
````

## tests/helpers.py

````python
"""Shared inputs for the tests: the notebook's portfolio and settle date."""

import conftest  # noqa: F401  (puts src/ on the path)
import sampleport

SECLIST = ["10yr UST", "5yr Bond Opt", "10yr UST", "10yr Swap", "10yr UKG",
           "FTE CDS", "CAC Index Futures", "FTE Equity", "GBPCash", "EURCash", "5yr UST"]
HOLDINGS = [20, -20, 30, -20, 25, 55, 7, 5, -10, 0, 0]
SUBPORTFOLIO = ["Government", "Government", "Swaps", "Swaps", "Government", "Credit",
                "Equity", "Equity", "Government", "Equity", "Government"]
SETTLEDATE = [2009, 1, 27, 0, 0, 0]


def fresh_data():
    """Return an independent copy of the SamplePort2.m data."""
    return sampleport.load_data()


def close(actual, expected, tolerance):
    """True if two numbers differ by no more than ``tolerance``."""
    return abs(actual - expected) <= tolerance
````

## tests/test_pv_and_dv01.py

````python
"""Unit tests: dates, instrument PVs and DV01s (bumping functions).

Expected values come from three sources, stated on each test:
  (M) values displayed by Mathematica in the notebook PDF (Table 1), compared
      after rounding the way the notebook rounds;
  (H) hand calculations / closed forms that must hold exactly;
  (P) properties that must hold for any correct translation.
"""

import math

import distfn
import formatting
from helpers import HOLDINGS, SECLIST, SETTLEDATE, close, fresh_data


def test_serialday_and_month_arithmetic():
    # (H) Mathematica: serialday[{1900,1,1,0,0,0}] = 2; 27-Jan-2009 is 39840 days later.
    assert distfn.serialday([1900, 1, 1]) == 2
    assert distfn.serialday(SETTLEDATE) - distfn.serialday([2008, 11, 15]) == 73
    assert distfn.date_plus_months([2009, 11, 15], -6) == [2009, 5, 15]
    assert distfn.date_plus_months([2009, 8, 31], 6) == [2010, 2, 28]   # clamps to month end
    assert distfn.date_plus_months([2009, 1, 15], -12) == [2008, 1, 15]


def test_pv_annuity_formula():
    # (H) 10 payments of 3 at 2% plus 100 at the end = 108.98258500...
    expected = 3 * (1 - 1.02 ** -10) / 0.02 + 100 * 1.02 ** -10
    assert close(distfn.pv(0.02, 10, 3, 100), expected, 1e-12)
    assert close(distfn.pv(0.05, 4, 5, 100), 100.0, 1e-12)             # par bond prices at 100


def test_bondprc_on_a_coupon_date_is_par_when_yield_equals_coupon():
    # (H) settle on a coupon date: clean price 100, accrued = one full coupon.
    parms = [4.0, [2018, 11, 15, 0, 0, 0], 2, "USD"]
    clean, accrued, dirty = distfn.bondprc(0.04, [2009, 5, 15, 0, 0, 0], parms)
    assert close(clean, 100.0, 1e-10) and close(accrued, 2.0, 1e-12)
    assert close(dirty, 102.0, 1e-10)


def test_bondprc_accrued_interest_uses_actual_days():
    # (H) 10yr UST 3.75% Nov-2018, settle 27-Jan-2009: 73 of 181 days accrued.
    parms = fresh_data()["secParmValues"][1]
    clean, accrued, dirty = distfn.bondprc(0.0253, SETTLEDATE, parms)
    assert close(accrued, 1.875 * 73 / 181, 1e-12)
    assert close(clean + accrued, dirty, 1e-12)
    assert 110 < clean < 111                                           # 3.75% coupon at 2.53% yield


def test_swap_and_cds_are_worth_zero_at_par():
    # (H) coupon equal to the discount rate gives PV 0.
    data = fresh_data()
    assert close(distfn.swappv([0.02, 0.008, 1], SETTLEDATE, 10, [2.8, 10, 2, "USD"], data), 0, 1e-6)
    cds = distfn.simpCDSpv([0.03, 0.015, 1], SETTLEDATE, 10, [1.5, 5, 2, "GBP"], data)
    assert close(cds, 0, 1e-6)


def test_bond_option_put_call_parity():
    # (P) "P" price minus "C" price = annuity * (forward - strike) * 100.
    arguments = (0.5, 0.005, 0.0178, 0.0168, 0.2, 5, 2)
    put = distfn.bondoptionprc(*arguments, "P")
    call = distfn.bondoptionprc(*arguments, "C")
    annuity = distfn.pv(0.0178 / 2, 10, 0.5, 0) / (1 + 0.005 / 2) ** 1.0
    assert close(put - call, annuity * (0.0178 - 0.0168) * 100, 1e-12)
    assert put > 0 and call > 0


def test_cash_and_equity_pv_convert_at_the_fx_rate():
    # (H) FX is foreign currency per USD, so GBP 10mn = USD 14mn at 1/1.4.
    data = fresh_data()
    assert close(distfn.pvposn("GBPCash", 10, SETTLEDATE, data["marketDataValues"], data), 14e6, 1e-6)
    assert close(distfn.pvposn("FTE Equity", 5, SETTLEDATE, data["marketDataValues"], data), 6.5e6, 1e-6)
    assert close(distfn.pvposn("CAC Index Futures", 7, SETTLEDATE, data["marketDataValues"], data),
                 9.1e6, 1e-6)


def test_equity_future_ignores_bumped_fx():
    # (P) quirk kept from eqtyFutpv: FX comes from the unbumped global data.
    data = fresh_data()
    bumped = list(data["marketDataValues"])
    bumped[data["marketDataNames"].index("EURFX")] *= 1.5
    base = distfn.pvposn("CAC Index Futures", 7, SETTLEDATE, data["marketDataValues"], data)
    assert distfn.pvposn("CAC Index Futures", 7, SETTLEDATE, bumped, data) == base


def test_security_dv01s_match_mathematica_table_1():
    # (M) Table 1 DV01 column, NumberForm[.., {5, 0}], in notebook order.
    displayed = ["18,292", "-3,029", "-4,254", "27,438", "-17,339", "-17,339", "28,555",
                 "4×10^7", "-79", "33,853", "-305,390", "9×10^6", "5×10^6", "7×10^6",
                 "6×10^6", "-1×10^7", "0", "0"]
    _, _, values = distfn.populateSecDV01s(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    shown = [formatting.number_form(value, 5, 0, digit_block=True)[0]
             for position_values in values for value in position_values]
    # FTEEqSpecific and EURFX on FTE Equity are both 6.5 million to within 1e-8, yet
    # display as 7x10^6 and 6x10^6: only Mathematica's operation order reproduces that.
    assert shown == displayed


def test_duplicate_securities_stay_separate_positions():
    # (P) "10yr UST" appears twice (20mn and 30mn); DV01s must scale 2:3, not merge.
    names, factor_names, values = distfn.populateSecDV01s(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert len(values) == len(SECLIST) == 11
    assert names[0] == names[2] == "10yr UST"
    assert close(values[2][0] / values[0][0], 1.5, 1e-9)


def test_dv01_is_linear_in_holding_and_zero_for_zero_holding():
    # (P) doubling a holding doubles its DV01; zero holding gives exactly 0.
    data = fresh_data()
    _, _, single = distfn.populateSecDV01s(["10yr UKG", "5yr UST"], [25, 0], SETTLEDATE, data)
    _, _, double = distfn.populateSecDV01s(["10yr UKG", "5yr UST"], [50, 0], SETTLEDATE, data)
    assert all(close(b, 2 * a, 1e-6 * abs(a)) for a, b in zip(single[0], double[0]))
    assert single[1] == [0.0]


def test_fx_and_equity_dv01_closed_forms():
    # (H) percent bump: DV01 = USD exposure for FX (per -100%) and beta * exposure for equity.
    data = fresh_data()
    _, _, values = distfn.populateSecDV01s(["GBPCash", "FTE Equity"], [-10, 5], SETTLEDATE, data)
    assert close(values[0][0], -14e6, 1e-3)
    # index beta 0.7: the symmetric percent bump gives 0.7 * 6.5mn up to O(h^2)
    assert close(values[1][0], 0.7 * 6.5e6, 100) and close(values[1][1], 6.5e6, 1e-3)
    assert close(values[1][2], 6.5e6, 1e-3)


def test_port_dv01s_sum_positions_in_risk_factor_order():
    # (P) portfolio DV01 = sum over positions; names follow riskFactorNames order.
    data = fresh_data()
    names, totals = distfn.populatePortDV01s(SECLIST, HOLDINGS, SETTLEDATE, data)
    _, factor_names, values = distfn.populateSecDV01s(SECLIST, HOLDINGS, SETTLEDATE, data)
    order = [data["riskFactorNames"].index(name) for name in names]
    assert order == sorted(order) and len(names) == 11
    expected = sum(value for row_names, row in zip(factor_names, values)
                   for name, value in zip(row_names, row) if name == "USDYld10yr")
    assert close(totals[names.index("USDYld10yr")], expected, 1e-9)
    assert math.isclose(expected, 18291.9 + 27437.9 - 17339.2, abs_tol=0.2)
````

## tests/test_risk_and_distributions.py

````python
"""Unit tests: VCV, volatilities, contributions, best hedges, replicating
portfolios and the distribution functions.

Sources of expected values: (M) displayed by Mathematica in the notebook PDF,
(H) hand calculation / closed form, (P) property that must hold.
"""

import itertools
import math

import numpy as np

import distfn
import formatting
import reports
from helpers import HOLDINGS, SECLIST, SETTLEDATE, SUBPORTFOLIO, close, fresh_data


def extended():
    """Extended risk results for the notebook portfolio."""
    return distfn.portVolbyVCVextended(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())


def test_vcv_is_symmetric_with_squared_vols_and_flipped_signs():
    # (H) yields and FX are both "down" bumps so their correlation keeps its sign;
    #     yield vs equity (down vs up) flips sign.
    data = fresh_data()
    vcv = distfn.populateVCV(["USDYld10yr", "GBPFX", "CACEqIndex"], data)
    assert np.allclose(vcv, vcv.T)
    assert close(vcv[0, 0], 7.148000008 ** 2, 1e-9)
    assert close(vcv[0, 1], 7.148000008 * 0.008110121 * 0.07932111, 1e-12)
    assert close(vcv[0, 2], -7.148000008 * 0.025365051 * -0.240000046, 1e-12)


def test_security_and_risk_factor_vols_match_table_1():
    # (M) Table 1 "Security Vol" column, NumberForm[.., {4, 0}].
    displayed = ["130,800", "20,170", "196,100", "136,500", "400,700", "65,540",
                 "230,800", "168,900", "113,500", "0", "0"]
    _, vols = distfn.secVolbyVCV(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert [formatting.number_form(vol, 4, 0, True)[0] for vol in vols] == displayed


def test_portfolio_volatility_matches_mathematica():
    # (M) 616,900 in three different notebook tables.
    vol = distfn.portVolbyVCV(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert formatting.accounting_form(vol)[0] == "616,900"
    assert close(vol, extended()["portvol"], 1e-9)


def test_contributions_sum_to_one_and_correlations_are_bounded():
    # (P) marginal contributions add up to 100%; |correlation| <= 1.
    result = extended()
    assert close(result["mcp"].sum(), 1.0, 1e-12)
    assert close(result["mcl"].sum(), result["portvol"], 1e-6)
    assert np.all(np.abs(result["corr"]) <= 1 + 1e-12)


def test_best_hedge_really_minimises_volatility():
    # (P) moving one DV01 to its best-hedge level gives volbesthedge, and any
    #     nearby level gives a higher volatility.
    result = extended()
    dv01s, vcv = result["portdv01s"], result["vcv"]
    for index in range(len(dv01s)):
        hedged = dv01s.copy()
        hedged[index] -= (vcv @ dv01s)[index] / vcv[index, index]
        best = math.sqrt(hedged @ vcv @ hedged)
        assert close(best, result["volbesthedge"][index], 1e-6)
        for nudge in (-0.01, 0.01):
            nudged = hedged.copy()
            nudged[index] += nudge * abs(dv01s[index] + 1)
            assert math.sqrt(nudged @ vcv @ nudged) >= best - 1e-9


def test_all_or_nothing_contribution_is_the_vol_change_when_zeroed():
    # (P) contallornot = portfolio vol - vol with that risk factor's DV01 set to 0.
    result = extended()
    for index in range(len(result["rflist"])):
        zeroed = result["portdv01s"].copy()
        zeroed[index] = 0.0
        expected = result["portvol"] - math.sqrt(zeroed @ result["vcv"] @ zeroed)
        assert close(result["contallornot"][index], expected, 1e-6)


def test_current_position_in_equivalents():
    # (H) besthedge + repport = DV01 / unit DV01: 13.65mn USD of CAC exposure = EUR 10.5mn.
    result = extended()
    index = result["rflist"].index("CACEqIndex")
    assert close(result["besthedge"][index] + result["repport"][index], 10.5, 1e-4)
    option_vol = result["rflist"].index("US5yrOptionVol")              # no equivalent security
    assert result["unitdv01s"][option_vol] == 0 and result["besthedge"][option_vol] == 0


def test_replicating_portfolio_first_step_is_the_best_single_asset():
    # (P) brute force over every single asset and every pair containing the first pick.
    result = extended()
    table = reports.bestReplicatePort(result["portdv01s"], result["vcv"],
                                      result["rflist"], result["unitdv01s"])
    part = result["vcv"] @ result["portdv01s"]
    variance = result["portdv01s"] @ part

    def explained(indexes):
        indexes = list(indexes)
        solution = np.linalg.solve(result["vcv"][np.ix_(indexes, indexes)], part[indexes])
        return part[indexes] @ solution / variance

    count = len(part)
    best_single = max(range(count), key=lambda i: explained([i]))
    assert table.loc[0, "Asset 1"] == result["rflist"][best_single]
    first = best_single
    best_pair = max((i for i in range(count) if i != first), key=lambda i: explained([first, i]))
    assert table.loc[1, "Asset 2"] == result["rflist"][best_pair]
    assert list(table["% Var"]) == sorted(table["% Var"])              # more assets explain more
    # stepwise is greedy: the exhaustive best triple can only do at least as well
    best_triple = max(explained(c) for c in itertools.combinations(range(count), 3))
    assert best_triple >= table.loc[2, "% Var"] / 100 - 1e-12


def test_replicating_portfolio_matches_mathematica():
    # (M) reportFunction1[[5]]: assets in order, % variance for 1, 3, 5 assets.
    result = extended()
    table = reports.bestReplicatePort(result["portdv01s"], result["vcv"],
                                      result["rflist"], result["unitdv01s"])
    assert list(table.loc[4, [f"Asset {k}" for k in range(1, 6)]]) == [
        "GBPYld10yr", "CACEqIndex", "GBPFX", "FTEEqSpecific", "USDYld10yr"]
    assert [round(table.loc[row, "% Var"], 1) for row in (0, 2, 4)] == [46.8, 86.7, 98.4]
    assert round(table.loc[0, "Eqv Pos'n 1"], 1) == 56.2


def test_subportfolio_contributions_sum_to_100_and_keep_duplicates_apart():
    # (P) contributions add up; the two "10yr UST" positions sit in different subportfolios.
    table = reports.volbySubPortfolio(SECLIST, HOLDINGS, SETTLEDATE, SUBPORTFOLIO, fresh_data())
    assert list(table["Subportfolio"]) == ["Overall", "Credit", "Equity", "Government", "Swaps"]
    assert close(table["Contribution"][1:].sum(), 100.0, 1e-9)
    swaps = float(table.loc[table["Subportfolio"] == "Swaps", "Exp Vol ($)"].iloc[0])
    assert formatting.accounting_form(swaps)[0] == "75,350"            # (M)


def test_empty_category_has_zero_vol_and_blank_correlation():
    # (M) Commodity row: vol 0, contribution 0, correlation blank.
    table = reports.reportFunction1(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())[0]
    commodity = table[table["Category"] == "Commodity"].iloc[0]
    assert commodity["Exp Vol ($)"] == 0 and commodity["Contribution"] == 0
    assert np.isnan(commodity["Correlation"])
    assert formatting.format_vol_summary(table)[6] == [("Commodity", None), ("0", 1.0),
                                                       ("0", 0.1), ("", None)]


def test_mixture_cdf_and_pdf_definitions():
    # (H) mixture = (1-a) N(0,s) + a N(0,b s), s = sigma / sqrt(1 - a + a b^2).
    sigma, alpha, beta = 2.0, 0.05, 3
    dist = distfn.normalmix(sigma)
    assert dist == ("normalmixture", 2.0, 0.05, 3)                     # DistFn1.m defaults
    s = sigma / math.sqrt(1 - alpha + alpha * beta ** 2)
    phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))             # noqa: E731
    assert close(distfn.cdf(dist, -3.0), (1 - alpha) * phi(-3 / s) + alpha * phi(-3 / (beta * s)), 1e-15)
    assert close(distfn.cdf(dist, 0.0), 0.5, 1e-15)
    step = 1e-5
    slope = (distfn.cdf(dist, 1 + step) - distfn.cdf(dist, 1 - step)) / (2 * step)
    assert close(distfn.pdf(dist, 1.0), slope, 1e-9)


def test_mixture_quantile_inverts_the_cdf():
    # (P) cdf(quantile(p)) = p across the range, including far tails.
    for alpha, beta in ((0.05, 3), (0.01, 5), (0.2, 10)):
        dist = distfn.normalmix(616900.0, alpha, beta)
        for probability in (1e-6, 1 / 255, 0.01, 0.3, 0.5, 0.9, 0.999):
            x = distfn.quantile(dist, probability)
            assert close(distfn.cdf(dist, x), probability, 1e-12)


def test_mixture_with_beta_one_is_a_normal():
    # (H) beta = 1 collapses the mixture to N(0, sigma).
    assert close(distfn.quantile(distfn.normalmix(3.0, 0.3, 1), 0.01),
                 distfn.quantile(distfn.normal(3.0), 0.01), 1e-10)


def test_student_quantiles_against_published_t_tables():
    # (H) t tables, 6 df: t(0.975) = 2.446912, t(0.99) = 3.142668; rescaled to unit SD.
    scale = math.sqrt(4 / 6)
    assert close(distfn.quantile(distfn.student(1.0), 0.975), 2.446912 * scale, 1e-6)
    assert close(distfn.quantile(distfn.student(1.0), 0.01), -3.142668 * scale, 1e-6)
    assert close(distfn.standard_student_cdf(0.0, 6), 0.5, 1e-15)


def test_quantile_rejects_bad_probabilities():
    for probability in (0, 1, -0.1, 1.5):
        try:
            distfn.quantile(distfn.normalmix(1.0), probability)
        except ValueError:
            continue
        raise AssertionError("quantile accepted an invalid probability")


def test_var_summary_matches_mathematica():
    # (M) varsumm output, AccountingForm[.., {4, 0}].
    table = reports.varsumm(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    shown = [formatting.accounting_form(value)[0] for value in table["Value"]]
    assert shown == ["616,900", "(1,640,000)", "(1,972,000)", "(1,680,000)", "(2,468,000)"]


def test_number_formats_reproduce_notebook_examples():
    # (M) examples read off the notebook PDF.
    assert formatting.number_form(39229880.7, 5, 0, True)[0] == "4×10^7"
    assert formatting.number_form(-305385.5, 5, 0, True)[0] == "-305,390"
    assert formatting.number_form(0.025365051, 5, 5)[0] == "0.02537"
    assert formatting.number_form(2.040043844, 4, 3)[0] == "2.040"
    assert formatting.number_form(-0.0712, 4, 3)[0] == "-0.071"
    assert formatting.accounting_form(-1640184.8)[0] == "(1,640,000)"
    assert formatting.number_form(0, 4, 1)[0] == "0"
````

## tests/test_tables.py

````python
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
````

## tests/run_tests.py

````python
"""Run every test without pytest:  python tests/run_tests.py

pytest gives nicer output (``python -m pytest``); this runner needs nothing
beyond the standard library, so the tests can be checked on any machine.
"""

import importlib
import sys
import traceback
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import conftest  # noqa: E402,F401  (puts src/ and the project root on the path)


def main():
    """Import each ``test_*.py`` module, call each ``test_*`` function, report."""
    passed, failed = 0, 0
    for path in sorted(TEST_DIR.glob("test_*.py")):
        module = importlib.import_module(path.stem)
        print(path.name)
        for name in sorted(vars(module)):
            if not name.startswith("test_"):
                continue
            try:
                getattr(module, name)()
                passed += 1
                print(f"  ok    {name}")
            except Exception:
                failed += 1
                print(f"  FAIL  {name}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
````

# Mathematica: scenario inputs and export script

## reference/original/inputs.m

````mathematica
(* Original portfolio: exactly the lines in Tables_Ch10.nb; SamplePort2.m unchanged *)
seclist = {"10yr UST","5yr Bond Opt","10yr UST","10yr Swap","10yr UKG","FTE CDS","CAC Index Futures","FTE Equity","GBPCash","EURCash","5yr UST"};
holdings = {20,-20,30,-20,25,55,7,5,-10,0,0};
subportfolio = {"Government","Government","Swaps","Swaps","Government","Credit","Equity","Equity","Government","Equity","Government"};
settledate = {2009,1,27,0,0,0};
````

## reference/scenario1/inputs.m

````mathematica
(* Scenario 1 - portfolio changes. Replace these lines in a copy of Tables_Ch10.nb
   saved as Tables_Ch10_scenario1.nb; SamplePort2.m unchanged.
   Changed: holdings 5 (25 -> -25), 10 (0 -> 15), 11 (0 -> 40); subportfolio 9 (Government -> Credit) *)
seclist = {"10yr UST","5yr Bond Opt","10yr UST","10yr Swap","10yr UKG","FTE CDS","CAC Index Futures","FTE Equity","GBPCash","EURCash","5yr UST"};
holdings = {20,-20,30,-20,-25,55,7,5,-10,15,40};
subportfolio = {"Government","Government","Swaps","Swaps","Government","Credit","Equity","Equity","Credit","Equity","Government"};
settledate = {2009,1,27,0,0,0};
````

## reference/scenario2/inputs.m

````mathematica
(* Scenario 2 - market-data change on the Scenario 1 portfolio.
   Load SamplePort2_scenario2.m (in this folder) instead of SamplePort2.m.
   Changed in marketDataValues: USDYld10yr .0253 -> .0353, GBPFX 1/1.4 -> 1/1.6 *)
seclist = {"10yr UST","5yr Bond Opt","10yr UST","10yr Swap","10yr UKG","FTE CDS","CAC Index Futures","FTE Equity","GBPCash","EURCash","5yr UST"};
holdings = {20,-20,30,-20,-25,55,7,5,-10,15,40};
subportfolio = {"Government","Government","Swaps","Swaps","Government","Credit","Equity","Equity","Credit","Equity","Government"};
settledate = {2009,1,27,0,0,0};
````

## reference/scenario3/inputs.m

````mathematica
(* Scenario 3 - new securities, new settlement date, fractional and offsetting holdings.
   SamplePort2.m unchanged except that settledate is set here AFTER loading it. *)
seclist = {"5yr UST","10yr UST","10yr UST","Swap201901","5yr UKG","10yr Bund","5yr Bund","SPX Index Futures","FTE Equity","FTE CDS","EURCash","GBPCash","5yr Bond Opt"};
holdings = {35,-12.5,12.5,-40,18,-22,30,-9,6,25,-8,0,10};
subportfolio = {"Rates","Rates","Macro","Macro","Rates","Macro","Rates","Equity","Equity","Credit","Macro","Credit","Rates"};
settledate = {2009,6,30,0,0,0};
````

## mathematica/RunScenarios.wl

````mathematica
(* ::Package:: *)

(* RunScenarios.wl
   Runs the ORIGINAL Mathematica code (SamplePort2.m, DistFn1.m and the notebook's
   table functions) for the original portfolio and every test scenario, and saves
   what Python is checked against:

     reference/<scenario>/tables.json   the nine tables, numbers at full precision
     reference/unit_values.json         function-level values for the unit tests

   Run from a terminal:   wolframscript -file mathematica/RunScenarios.wl
   or open this file in Mathematica and choose Evaluation > Run Package.

   Numbers are saved unrounded; verify.py rounds them with the notebook's
   NumberForm / AccountingForm rules before comparing. *)

mmaDir = DirectoryName[$InputFileName];
If[mmaDir === "", mmaDir = NotebookDirectory[]];
projectDir = ParentDirectory[mmaDir];
refDir = FileNameJoin[{projectDir, "reference"}];

(* Strip display wrappers, keeping the number inside *)
cleanTable[t_] := N[t /. {Style[s_, ___] :> s, SpanFromLeft -> "",
     (NumberForm | AccountingForm)[v_, ___] :> v}];

(* Holdings table for ALL positions (the notebook's Out[38] hard-codes n = 9) *)
holdingsTable[seclist_, holdings_, subportfolio_] :=
  Join[{{"Security", "Amount (mn local)", "Curr", "Subportfolio"}},
   Table[{seclist[[i]], holdings[[i]],
     fxsymb[seclist[[i]], {"$", "\[Yen]", "\[Sterling]", "\[Euro]"}, {"USD", "JPY", "GBP", "EUR"}][[1]],
     subportfolio[[i]]}, {i, Length[seclist]}]];

loadCode[sampleFile_] := (
   Get[sampleFile];
   Get[FileNameJoin[{mmaDir, "DistFn1.m"}]];
   Get[FileNameJoin[{mmaDir, "TableFunctions.wl"}]];);

runScenario[name_, sampleFile_] := Module[{xx, yy, out, dir},
   loadCode[sampleFile];                                      (* resets all market data *)
   dir = FileNameJoin[{refDir, name}];
   Get[FileNameJoin[{dir, "inputs.m"}]];                      (* seclist, holdings, subportfolio, settledate *)
   xx = reportFunction1[seclist, holdings, settledate];
   yy = volbySubPortfolio[seclist, holdings, settledate, subportfolio];
   out = {
     "holdings" -> cleanTable[holdingsTable[seclist, holdings, subportfolio]],
     "table1" -> cleanTable[First[displayRF[seclist, holdings, settledate]]],
     "category" -> cleanTable[xx[[1]]],
     "top_contributors" -> cleanTable[xx[[2]]],
     "single_hedge" -> cleanTable[xx[[3]]],
     "best_hedges" -> cleanTable[xx[[4]]],
     "replicating" -> cleanTable[xx[[5]]],
     "subportfolio" -> cleanTable[yy],
     "var" -> cleanTable[varsumm[seclist, holdings, settledate]]};
   Export[FileNameJoin[{dir, "tables.json"}], out, "JSON"];
   Print["Saved ", FileNameJoin[{dir, "tables.json"}]];
   ];



runScenario["scenario1", FileNameJoin[{mmaDir, "SamplePort2.m"}]];
runScenario["scenario2", FileNameJoin[{refDir, "scenario2", "SamplePort2_scenario2.m"}]];
runScenario["scenario3", FileNameJoin[{mmaDir, "SamplePort2.m"}]];

(* ---- Function-level values for the unit tests (original portfolio) ---- *)
loadCode[FileNameJoin[{mmaDir, "SamplePort2.m"}]];
Get[FileNameJoin[{refDir, "original", "inputs.m"}]];
Module[{sec, port, eqv, ext, rep, unit},
  sec = populateSecDV01s[seclist, holdings, settledate];
  port = populatePortDV01s[seclist, holdings, settledate];
  eqv = populateEqvDV01s[seclist, settledate];
  ext = portVolbyVCVextended[seclist, holdings, settledate];
  rep = bestReplicatePort[ext[[12]], ext[[13]], ext[[8]], ext[[9]]];
  unit = {
    "serialday_settle" -> serialday[settledate],
    "pv_example" -> N[pv[0.02, 10, 3, 100]],
    "bondprc_10yrUST" -> N[bondprc[0.0253, settledate, secParmValues[[2]]]],
    "bondoptionprc" -> N[bondoptionprc[0.5, 0.005, 0.0178, 0.0168, 0.2, 5, 2, "C"]],
    "pvPort" -> N[pvPort[seclist, holdings, settledate, marketDataValues]],
    "secDV01s" -> N[sec[[3]]],
    "portDV01Names" -> port[[1]], "portDV01s" -> N[port[[2]]],
    "eqvDV01Names" -> eqv[[1]], "eqvDV01s" -> N[eqv[[2]]],
    "vcv" -> N[populateVCV[port[[1]]]],
    "secVols" -> N[secVolbyVCV[seclist, holdings, settledate][[2]]],
    "rfVols" -> N[rfVolbyVCV[seclist, holdings, settledate][[2]]],
    "portvol" -> N[ext[[1]]], "mcl" -> N[ext[[2]]], "mcp" -> N[ext[[3]]],
    "contallornot" -> N[ext[[4]]], "besthedge" -> N[ext[[5]]], "volbesthedge" -> N[ext[[6]]],
    "corr" -> N[ext[[10]]], "repport" -> N[ext[[11]]],
    "replicate_vols" -> N[rep[[2]]], "replicate_pctvar" -> N[rep[[3]]],
    "replicate_names" -> rep[[5]], "replicate_amounts" -> N[rep[[7]]],
    "mix_pdf" -> N[pdf[normalmix[1.], -2.]],
    "mix_cdf" -> N[cdf[normalmix[1.], -2.]],
    "mix_quantile" -> N[quantile[normalmix[1.], 0.01]],
    "var_normal" -> N[var[normal, 1/255, 1.]],
    "var_student" -> N[var[student, 1/255, 1.]],
    "var_normalmix" -> N[var[normalmix, 1/255, 1.]]};
  Export[FileNameJoin[{refDir, "unit_values.json"}], unit, "JSON"];
  Print["Saved ", FileNameJoin[{refDir, "unit_values.json"}]];
  ];
````

# Mathematica: table functions extracted from Tables_Ch10.nb

## mathematica/TableFunctions.wl

````mathematica
(* ::Package:: *)

(* TableFunctions.wl
   The table/report functions of Tables_Ch10.nb, copied out of the notebook's
   Input cells as plain text so that a script can load them (see RunScenarios.wl).
   The code is unchanged; only the notebook's special operator characters
   (rule arrow, <=, ==, !=) are written in plain ASCII.
   Requires SamplePort2.m and DistFn1.m to be loaded first. *)


tableContributers[ordering_,rflist_,portvol_,volexplained_,combvol_,nav_]:=Module[{xx2,xx3,k},
k = Length[ordering];
xx2 = {{"", "Exp Vol", "", "Curr Pos'n", "Trade to best", "% Reduction in Vol to", SpanFromLeft},
   {"", "(1-sig P&L)", "Contribution", "(mn eqv)", "Hedge (eqv)", "Best Hedge", "Zero Pos'n"}};
xx3 = Join[xx2, Table[{rflist[[ordering[[i]]]],
     If[nav>1,
NumberForm[100*portvol[[7]][[ordering[[i]]]]/nav, {5, 4}], (* RF vol in percentage *)
AccountingForm[portvol[[7]][[ordering[[i]]]], {4, 0}, DigitBlock -> 3, NumberPoint -> ""]], (* RF vol *)
     NumberForm[100*portvol[[3]][[ordering[[i]]]], {4, 1}], (* Cont'n *)
     NumberForm[(portvol[[5]][[ordering[[i]]]] + portvol[[11]][[ordering[[i]]]]), {4, 1}], (* Original pos'n *)
     NumberForm[-portvol[[11]][[ordering[[i]]]], {4, 1}], (* Trade to best hedge *)
     NumberForm[volexplained[[ordering[[i]]]], {4, 1}], (* Vol explained % *)
     NumberForm[100*portvol[[4]][[ordering[[i]]]]/combvol, {4, 1}](* Vol explained % *)},
    {i, 1, k}]]
]


reportFunction1[seclist_,holdings_,settledate_,nav_] := Module[{xx,portvol,yy,x,y,combvol,i,table,rflist,xx2,xx3,xx4,xx5,xx6,zz,volexplained,ordering,replicateport},
portvol = portVolbyVCVextended[seclist,holdings,settledate];
(* 
1. portfolio volatility
2. list of marginal contributions (vector) in levels (for risk factors)
3. marginal contributions proportional
4. All-or-nothing contribution (change in vol when this pos'n is set to zero)
5. Best hedge position (in same units as inputholdingsItalic)-must fix because by RFs not securities
6. Volatility at best hedge
7. Stand-alone volatilities of individual risk factors
8. RF list (remember that although seclistItalic Italicis input,risk is done by RFs
9. DV01s by RFs per 1 unit holdings
10. Correlations of RFs with portfolio
11. Replicating position (=original-best hedge) 
12. DV01s by RFs (actual holdings)
13. VCV matrix   *)
combvol=portvol[[1]];
rflist = portvol[[8]];
volexplained = 100.0*(1 - portvol[[6]]/combvol);
yy={"FI - rates","FI - swap spreads","Credit","Equity","Commodity","FX","Volatility"}; (* List of headings - RFs are labeled by these *)
xx =Flatten[ Table[Pick[riskFactorCategory,riskFactorNames,rflist[[i]]],{i,1,Length[rflist]}]]; (* This is a list, in same order as rflist, of headings *)
zz=ConstantArray[0,Length[yy]]; (* Empty list into which vols will be insterted *)
For[i=1,i<=Length[yy],i++, (* Calculate vol by category *)
xx4 = ConstantArray[0,Length[xx]];
xx3=Flatten[Position[xx,yy[[i]]]];
xx4[[xx3]]=portvol[[12]][[xx3]]; (* DV01s for this category *)
zz[[i]]=Sqrt[xx4.portvol[[13]].xx4]; (* vol for this category *)
];
If[nav>1,
xx2=Table[{yy[[i]],NumberForm[100*zz[[i]]/nav,{5,4}],NumberForm[100*(x=Total[Pick[portvol[[3]],xx,yy[[i]]]]),{4,1}],If[zz[[i]]>0,NumberForm[x*combvol/zz[[i]],{4,3}],""]},{i,1,Length[yy]}];
table = {{"","Exp Vol (%)","Contribution","Correlation"},
{"Overall",NumberForm[100*combvol/nav,{5,4}],"100.0","with portfolio"}};,
xx2=Table[{yy[[i]],AccountingForm[zz[[i]],{4,0},DigitBlock->3,NumberPoint->""],NumberForm[100*(x=Total[Pick[portvol[[3]],xx,yy[[i]]]]),{4,1}],If[zz[[i]]>0,NumberForm[x*combvol/zz[[i]],{4,3}],""]},{i,1,Length[yy]}];
table = {{"","Exp Vol ($)","Contribution","Correlation"},
{"Overall",AccountingForm[combvol,{4,0},DigitBlock->3,NumberPoint->""],"100.0","with portfolio"}};
];
table=Join[table,xx2];
ordering = Ordering[-portvol[[3]],3]; (* top 5 contributers to vol *)
xx3=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
ordering = Ordering[portvol[[3]],1]; (* top 3 neg contributers to vol *)
xx4=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
ordering = Ordering[portvol[[6]],3]; (* top 5 best single hedges *)
xx5=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
(* Now format the "Replicating Portfolio" table *)
replicateport=bestReplicatePort[portvol[[12]],portvol[[13]],portvol[[8]],portvol[[9]]];
xx6={{"","One Asset",SpanFromLeft,"Three Assets",SpanFromLeft,"Five Assets",SpanFromLeft},{"","% Var","% Vol","% Var","% Vol","% Var","% Vol"},
Join[{"%Var / %Vol Explained"},Flatten[Table[{NumberForm[100*replicateport[[3,i]],{4,1}],NumberForm[100*replicateport[[4,i]],{4,1}]},{i,{1,3,5}}]]],
{"","Asset","Eqv Pos'n","Asset","Eqv Pos'n","Asset","Eqv Pos'n"},
Join[{"Asset / Eqv Pos'n"},Flatten[Table[{replicateport[[5,1]],NumberForm[replicateport[[7,i,1]],{4,1}]},{i,{1,3,5}}]]],
Join[{"","",""},Flatten[Table[{replicateport[[5,2]],NumberForm[replicateport[[7,i,2]],{4,1}]},{i,{3,5}}]]],Join[{"","",""},Flatten[Table[{replicateport[[5,3]],NumberForm[replicateport[[7,i,3]],{4,1}]},{i,{3,5}}]]],
{"","","","","",replicateport[[5,4]],NumberForm[replicateport[[7,5,4]],{4,1}]},
{"","","","","",replicateport[[5,5]],NumberForm[replicateport[[7,5,5]],{4,1}]}
};

table = {table,xx3,xx4,xx5,xx6}
]


reportFunction1[seclist_, holdings_, settledate_] :=reportFunction1[seclist,holdings,settledate,1]


volbySubPortfolio[seclist_,holdings_,settledate_,subportfolio_]:=Module[{x1,x2,x3,x4,subportlist,noclass,results,i,j,xhold,table,partial,zeros},
subportlist=Union[subportfolio];    (* List of unique asset classes *)
noclass=Length[subportlist];          (* Number of asset classes *)
zeros=ConstantArray[0,Length[holdings]];  (* used for holding subportfolio holdings *)
results =  portVolbyVCVextended[seclist,holdings,settledate];  (* for complete portfolio *)
For[i=1,i<=noclass,i++,
x1=Flatten[Position[subportfolio,subportlist[[i]]]];   (* indexes of this asset class in seclist *)
xhold = zeros;xhold[[x1]]=holdings[[x1]];  (* insert holdings for this subportfolio *)
x2 = portVolbyVCVextended[seclist,xhold,settledate];
results = Join[results,x2];  (* This stacks additional results onto the end - each "results" is 13 long, so two stacked is 26, 3 is 39, ... *)
];
partial = results[[13]].results[[12]]; (* Matrix multiplication of VCV . Delta *)
table={{"","Exp Vol ($)","Contribution","Correlation"},
{"Overall",AccountingForm[x1=results[[1]],{4,0},DigitBlock->3,NumberPoint->""],"100.0","with portfolio"}};
table = Join[table,
Table[{subportlist[[i]],AccountingForm[x2=results[[13*i+1]],{4,0},DigitBlock->3,NumberPoint->""],NumberForm[x3=100*(results[[13*i+12]].partial)/(x1^2),{4,1}],If[x2>0,NumberForm[x3*x1/(100*x2),{4,3}],""]},{i,1,noclass}]]
]


varsumm[seclist_,holdings_,settledate_]:=Module[{x1,x2,alpha,beta,mixfact,normalmix},
x1=portVolbyVCV[seclist,holdings,settledate];
alpha=0.01;beta=5;mixfact = Sqrt[1-alpha + alpha*beta*beta];
normalmix[vol_]:=MixtureDistribution[{1-alpha,alpha},{NormalDistribution[0,vol/mixfact],NormalDistribution[0,beta*vol/mixfact]}];
x2 = {{"VOLATILITY and 1-ot-of 255 VaR",SpanFromLeft},
{"Volatility",AccountingForm[x1,{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Normal",AccountingForm[Quantile[NormalDistribution[0,x1],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Student-t (6df)",AccountingForm[x1*Sqrt[4/6]*Quantile[StudentTDistribution[6],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Normal Mix (\[Alpha]=1% \[Beta]=5)",AccountingForm[Quantile[normalmix[x1],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR 4-sigma rule-of-thumb",AccountingForm[-4*x1,{4,0},DigitBlock->3,NumberPoint->""]}}
]


displayRF[seclist_,holdings_,settledate_] := Module[{x,xx,y,z,secDV01s,outTable,i,j,symb,isocode,vcv,secVols,rfVols},
symb = {"$","\[Yen]","\[Sterling]","\[Euro]"};
isocode = {"USD","JPY","GBP","EUR"};
secDV01s = Transpose[populateSecDV01s[seclist,holdings,settledate]];
secVols = Transpose[secVolbyVCV[seclist,holdings,settledate]];
rfVols = Transpose[rfVolbyVCV[seclist,holdings,settledate]];
outTable={{"Security","Notional","Security Vol","RIsk Factor","DV01","DV01 units","RF unit Vol","RF pos'n Vol"}};
For[i=1,i<=Length[seclist],i++,   (* Loop through securities *)
x = fxsymb[seclist[[i]],symb,isocode];
x = x[[1]]<>ToString[holdings[[i]]]<>"mn";
y =NumberForm[secVols[[i,2]],{4,0},DigitBlock->3,NumberPoint->""];
x = {{Style[seclist[[i]],Bold],x,y,"","","","",""}};
outTable=Join[outTable,x];
For [j=1,j<=Length[secDV01s[[i,2]]],j++,   (* Loop through RFs for each security and figure out RF items *)
x = {{"","","",secDV01s[[i,2,j]],NumberForm[secDV01s[[i,3,j]],{5,0},DigitBlock->3,NumberPoint->""],"","",""}};
y=Pick[riskFactorBumpTypes,riskFactorNames,x[[1,4]]][[1]];  (* Figure out bump type *)
x[[1,6]]=y;      (* put into line *)
z=Pick[marketVols,marketDataNames,x[[1,4]]][[1]];  (* Figure out vol *)
xx =NumberForm[z,If[y=="percent",{5,5},{4,3}]];
x[[1,7]] = xx;     (* insert vol in *)
y =NumberForm[Abs[secDV01s[[i,3,j]]*z],{4,0},DigitBlock->3,NumberPoint->""];
x[[1,8]]=y;          (* insert rf vol for this position *)
outTable = Join[outTable,x];      (* tack on line of RF data *)
];
];
Grid[outTable,Frame->All]
]


bestReplicatePort[delta_,sigma_,rfnames_,rfunitDV01s_] := Module[{x,y,z,part,portvar,dstar,index,portvar5,varchk,i,j,k,portsize,partint,sigmaint,dstarint,varint,dstarint5,nosec,portvarPercent,names,amounts,portvolPercent},
(* The 'inputs' are                                           *)
(*    delta - column vector of deltas or portfolio weights    *)
(*    sigma - variance-covariance matrix sigma                *)
(* The portfolio variance is                                  *)
(*     d' * sigma * d                                         *)
(* We need the following as intermediate                      *)
(*     part = sigma * d - column vector of partial multiplication    *)
(* The variance when the 'best hedges' for i,j,k is           *)
(*     portvar - part[i j k]' * inv(sigma[i j k, i j k]) * part[i j k]  *)
(* so the variance reduction                                 *)
(*     part[i j k]' * inv(sigma[i j k, i j k]) * part[i j k]  *)
(* The coefficients (weights or delta) of the best hedges are *)
(*     dstar = -inv(sigma[i j k]) * part[i j k] + delta[i j k]    *)
(* so we want the intermediate results                        *)
(*     dstar_int = inv(sigma[i j k]) * part[i j k]         *)
(* to get it as                                               *)
(*     dstar_int = part[i j k] / sigma[i j k]              *)
(* and then                                                   *)
(*     var_bh = part[ ]' * dstar_int                       *)
(* and save dstarint, var_bh, and {i,j,k} for later comparison   *)
(*  Output  
1. Overall Port vol
2. Port vol for each replicating
3. Percent por variance explained
4. Percent port volatility explained
5. RF names
6. Ragged array of RF deltas (DV01s)
7. Ragged array of RF amounts (if there are eqvs)  *)
nosec=5;   (* Build replicating portfolios for 1-5 securities *)
portsize=Length[delta];
part=sigma.delta;
portvar=delta.part;
index=ConstantArray[0,nosec];
dstarint5={{}}; (* These will be ragged array of positions, names, etc *)
 names={}; amounts={{}};  
portvar5=ConstantArray[0,nosec];
For[i=1,i<=nosec,i++,
varchk=portvar;
For[j=1,j<=portsize,j++, (* Loop through assets *)
If[MemberQ[index,j],Null,  (* If this asset has not been selected yet then go *)
index[[i]]=j; (* Add this asset's index to the list of selected assets *)
partint=part[[index[[1;;i]]]]; (* Select out appropriate assets *)
sigmaint=sigma[[index[[1;;i]],index[[1;;i]]]];
dstarint=LinearSolve[sigmaint,partint];  (* Intermediate result *)
varint=portvar-partint.dstarint;  (* Variance for this set of assets *)
If[varint<varchk,  (* If lowest so far *)
varchk=varint;
k=j;,                            (* Keep track of index *)
Null;];
];   (* End If for MemberQ *)
];  (* End looping over assets *)
index[[i]]=k;                         (* Now do everything for the best of this loop *)
partint=part[[index[[1;;i]]]];
sigmaint=sigma[[index[[1;;i]],index[[1;;i]]]];
portvar5[[i]]=varchk;
dstarint5=Join[dstarint5,{LinearSolve[sigmaint,partint]}];  (* This is poition at best "best hedge" *)
names=Join[names,{rfnames[[k]]}];
y={};
For[j=1,j<=i,j++,
If[rfunitDV01s[[index[[j]]]] != 0,x=dstarint5[[i+1,j]]/rfunitDV01s[[index[[j]]]],x=0];
y=Join[y,{x}];
];
amounts=Join[amounts,{y}];
];      (* End loop for replicates *)
portvarPercent=1-(portvar5/portvar);   (* Percentage of original portfolio variance explained *)
portvolPercent = 1 - (Sqrt[portvar5]/Sqrt[portvar]); (* Percentage vol explained *)
dstarint5=dstarint5[[2;;6]];  (* Drop off first element (empty) *)
amounts=amounts[[2;;6]];
{Sqrt[portvar],Sqrt[portvar5],portvarPercent,portvolPercent,names,dstarint5,amounts}
]


Off[NumberForm::sigz]
````

# Configuration

## requirements.txt

````text
# Python 3.15 (developed and verified on 3.15.0)
numpy==2.5.4
pandas==3.0.6
# Optional: nicer test output.  Without it, run: python tests/run_tests.py
pytest
````
