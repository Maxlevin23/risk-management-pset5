(* Scenario 3 - new securities, new settlement date, fractional and offsetting holdings.
   SamplePort2.m unchanged except that settledate is set here AFTER loading it. *)
seclist = {"5yr UST","10yr UST","10yr UST","Swap201901","5yr UKG","10yr Bund","5yr Bund","SPX Index Futures","FTE Equity","FTE CDS","EURCash","GBPCash","5yr Bond Opt"};
holdings = {35,-12.5,12.5,-40,18,-22,30,-9,6,25,-8,0,10};
subportfolio = {"Rates","Rates","Macro","Macro","Rates","Macro","Rates","Equity","Equity","Credit","Macro","Credit","Rates"};
settledate = {2009,6,30,0,0,0};
