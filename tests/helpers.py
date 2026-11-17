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
