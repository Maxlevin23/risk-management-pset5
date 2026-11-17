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
