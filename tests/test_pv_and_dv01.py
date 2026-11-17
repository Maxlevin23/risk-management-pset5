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
    # EURFX on FTE Equity is exactly 6.5 million: a rounding boundary (see README).
    mismatches = [(a, b) for a, b in zip(shown, displayed) if a != b]
    assert mismatches in ([], [("7×10^6", "6×10^6")]), mismatches


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
