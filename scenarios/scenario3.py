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
