"""Part II unit tests: every translated function against Mathematica, same inputs.

Expected values are in ``reference/unit_values.json``, produced by running the
ORIGINAL DistFn1.m / SamplePort2.m / Tables_Ch10.nb functions in Mathematica
15.0.1 (``mathematica/RunScenarios.wl``) on the notebook portfolio.  Each test
calls the Python translation with the same inputs and requires agreement to a
relative tolerance of 1e-9 (absolute 1e-6 for values near zero), far tighter
than anything the reports display.

The tests follow the five groups the assignment lists:
    1. instrument PVs and DV01s (bumping functions)
    2. risk-factor volatilities and the variance-covariance calculation
    3. volatility contributions and correlations
    4. best-hedge and replicating-portfolio routines
    5. the mixture-of-normals distribution functions (CDF and inverse CDF)
"""

import json

import numpy as np

import conftest
import distfn
import reports
from helpers import HOLDINGS, SECLIST, SETTLEDATE, fresh_data

UNIT_VALUES = conftest.PROJECT_DIR / "reference" / "unit_values.json"
RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-6


def mathematica(name):
    """Return one Mathematica reference value by name."""
    return json.loads(UNIT_VALUES.read_text())[name]


def agrees(actual, expected):
    """True if Python and Mathematica values agree element by element."""
    return np.allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float),
                       rtol=RELATIVE_TOLERANCE, atol=ABSOLUTE_TOLERANCE)


def flatten(ragged):
    """Flatten a list of lists (Mathematica ragged arrays) into one list."""
    return [value for row in ragged for value in row]


def extended():
    """portVolbyVCVextended for the notebook portfolio."""
    return distfn.portVolbyVCVextended(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())


# --- 1. Instrument PVs and DV01s -------------------------------------------------

def test_serialday_matches_mathematica():
    assert distfn.serialday(SETTLEDATE) == mathematica("serialday_settle")


def test_pv_matches_mathematica():
    assert agrees(distfn.pv(0.02, 10, 3, 100), mathematica("pv_example"))


def test_bondprc_matches_mathematica():
    parms = fresh_data()["secParmValues"][1]                     # 10yr UST
    assert agrees(distfn.bondprc(0.0253, SETTLEDATE, parms), mathematica("bondprc_10yrUST"))


def test_bondoptionprc_matches_mathematica():
    price = distfn.bondoptionprc(0.5, 0.005, 0.0178, 0.0168, 0.2, 5, 2, "C")
    assert agrees(price, mathematica("bondoptionprc"))


def test_pvPort_matches_mathematica_for_every_position():
    data = fresh_data()
    values = distfn.pvPort(SECLIST, HOLDINGS, SETTLEDATE, data["marketDataValues"], data)
    assert agrees(values, mathematica("pvPort"))


def test_populateSecDV01s_matches_mathematica():
    _, _, dv01s = distfn.populateSecDV01s(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert agrees(flatten(dv01s), flatten(mathematica("secDV01s")))


def test_populatePortDV01s_matches_mathematica():
    names, dv01s = distfn.populatePortDV01s(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert names == mathematica("portDV01Names")
    assert agrees(dv01s, mathematica("portDV01s"))


def test_populateEqvDV01s_matches_mathematica():
    names, dv01s = distfn.populateEqvDV01s(SECLIST, SETTLEDATE, fresh_data())
    assert names == mathematica("eqvDV01Names")
    assert agrees(dv01s, mathematica("eqvDV01s"))


# --- 2. Risk-factor volatilities and the variance-covariance matrix --------------

def test_populateVCV_matches_mathematica():
    vcv = distfn.populateVCV(mathematica("portDV01Names"), fresh_data())
    assert agrees(vcv, mathematica("vcv"))


def test_secVolbyVCV_matches_mathematica():
    _, vols = distfn.secVolbyVCV(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert agrees(vols, mathematica("secVols"))


def test_rfVolbyVCV_matches_mathematica():
    _, vols = distfn.rfVolbyVCV(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert agrees(vols, mathematica("rfVols"))


def test_portVolbyVCV_matches_mathematica():
    vol = distfn.portVolbyVCV(SECLIST, HOLDINGS, SETTLEDATE, fresh_data())
    assert agrees(vol, mathematica("portvol"))


# --- 3. Volatility contributions and correlations --------------------------------

def test_marginal_contributions_match_mathematica():
    result = extended()
    assert agrees(result["portvol"], mathematica("portvol"))
    assert agrees(result["mcl"], mathematica("mcl"))
    assert agrees(result["mcp"], mathematica("mcp"))


def test_all_or_nothing_contribution_matches_mathematica():
    assert agrees(extended()["contallornot"], mathematica("contallornot"))


def test_correlations_with_portfolio_match_mathematica():
    assert agrees(extended()["corr"], mathematica("corr"))


# --- 4. Best hedges and replicating portfolios -----------------------------------

def test_best_hedge_positions_and_volatility_match_mathematica():
    result = extended()
    assert agrees(result["besthedge"], mathematica("besthedge"))
    assert agrees(result["volbesthedge"], mathematica("volbesthedge"))
    assert agrees(result["repport"], mathematica("repport"))


def test_bestReplicatePort_matches_mathematica():
    result = extended()
    table = reports.bestReplicatePort(result["portdv01s"], result["vcv"],
                                      result["rflist"], result["unitdv01s"])
    names = [table.loc[4, f"Asset {slot}"] for slot in range(1, 6)]
    assert names == mathematica("replicate_names")
    assert agrees(table["% Var"] / 100, mathematica("replicate_pctvar"))
    port_vol = result["portvol"]
    residual_vols = port_vol * (1 - table["% Vol"] / 100)
    assert agrees(residual_vols, mathematica("replicate_vols"))
    amounts = [[table.loc[size - 1, f"Eqv Pos'n {slot}"] for slot in range(1, size + 1)]
               for size in range(1, 6)]
    assert agrees(flatten(amounts), flatten(mathematica("replicate_amounts")))


# --- 5. Distribution functions (DistFn1.m defaults: alpha = 0.05, beta = 3) -------

def test_mixture_pdf_matches_mathematica():
    assert agrees(distfn.pdf(distfn.normalmix(1.0), -2.0), mathematica("mix_pdf"))


def test_mixture_cdf_matches_mathematica():
    assert agrees(distfn.cdf(distfn.normalmix(1.0), -2.0), mathematica("mix_cdf"))


def test_mixture_inverse_cdf_matches_mathematica():
    assert agrees(distfn.quantile(distfn.normalmix(1.0), 0.01), mathematica("mix_quantile"))


def test_var_functions_match_mathematica():
    assert agrees(distfn.var(distfn.normal, 1 / 255, 1.0), mathematica("var_normal"))
    assert agrees(distfn.var(distfn.student, 1 / 255, 1.0), mathematica("var_student"))
    assert agrees(distfn.var(distfn.normalmix, 1 / 255, 1.0), mathematica("var_normalmix"))
