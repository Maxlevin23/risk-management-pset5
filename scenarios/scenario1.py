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
