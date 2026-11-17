(* Scenario 2 - market-data change on the Scenario 1 portfolio.
   Load SamplePort2_scenario2.m (in this folder) instead of SamplePort2.m.
   Changed in marketDataValues: USDYld10yr .0253 -> .0353, GBPFX 1/1.4 -> 1/1.6 *)
seclist = {"10yr UST","5yr Bond Opt","10yr UST","10yr Swap","10yr UKG","FTE CDS","CAC Index Futures","FTE Equity","GBPCash","EURCash","5yr UST"};
holdings = {20,-20,30,-20,-25,55,7,5,-10,15,40};
subportfolio = {"Government","Government","Swaps","Swaps","Government","Credit","Equity","Equity","Credit","Equity","Government"};
settledate = {2009,1,27,0,0,0};
