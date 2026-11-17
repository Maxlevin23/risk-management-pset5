(* Scenario 1 - portfolio changes. Replace these lines in a copy of Tables_Ch10.nb
   saved as Tables_Ch10_scenario1.nb; SamplePort2.m unchanged.
   Changed: holdings 5 (25 -> -25), 10 (0 -> 15), 11 (0 -> 40); subportfolio 9 (Government -> Credit) *)
seclist = {"10yr UST","5yr Bond Opt","10yr UST","10yr Swap","10yr UKG","FTE CDS","CAC Index Futures","FTE Equity","GBPCash","EURCash","5yr UST"};
holdings = {20,-20,30,-20,-25,55,7,5,-10,15,40};
subportfolio = {"Government","Government","Swaps","Swaps","Government","Credit","Equity","Equity","Credit","Equity","Government"};
settledate = {2009,1,27,0,0,0};
