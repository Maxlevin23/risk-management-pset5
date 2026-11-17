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
