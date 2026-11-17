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
