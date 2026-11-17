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
