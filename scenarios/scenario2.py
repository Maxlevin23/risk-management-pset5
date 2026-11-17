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
