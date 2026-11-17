(* ::Package:: *)

(* RunScenarios.wl
   Runs the ORIGINAL Mathematica code (SamplePort2.m, DistFn1.m and the notebook's
   table functions) for the original portfolio and every test scenario, and saves
   what Python is checked against:

     reference/<scenario>/tables.json   the nine tables, numbers at full precision
     reference/unit_values.json         function-level values for the unit tests

   Run from a terminal:   wolframscript -file mathematica/RunScenarios.wl
   or open this file in Mathematica and choose Evaluation > Run Package.

   Numbers are saved unrounded; verify.py rounds them with the notebook's
   NumberForm / AccountingForm rules before comparing. *)

mmaDir = DirectoryName[$InputFileName];
If[mmaDir === "", mmaDir = NotebookDirectory[]];
projectDir = ParentDirectory[mmaDir];
refDir = FileNameJoin[{projectDir, "reference"}];

(* Strip display wrappers, keeping the number inside *)
cleanTable[t_] := N[t /. {Style[s_, ___] :> s, SpanFromLeft -> "",
     (NumberForm | AccountingForm)[v_, ___] :> v}];

(* Holdings table for ALL positions (the notebook's Out[38] hard-codes n = 9) *)
holdingsTable[seclist_, holdings_, subportfolio_] :=
  Join[{{"Security", "Amount (mn local)", "Curr", "Subportfolio"}},
   Table[{seclist[[i]], holdings[[i]],
     fxsymb[seclist[[i]], {"$", "\[Yen]", "\[Sterling]", "\[Euro]"}, {"USD", "JPY", "GBP", "EUR"}][[1]],
     subportfolio[[i]]}, {i, Length[seclist]}]];

loadCode[sampleFile_] := (
   Get[sampleFile];
   Get[FileNameJoin[{mmaDir, "DistFn1.m"}]];
   Get[FileNameJoin[{mmaDir, "TableFunctions.wl"}]];);

runScenario[name_, sampleFile_] := Module[{xx, yy, out, dir},
   loadCode[sampleFile];                                      (* resets all market data *)
   dir = FileNameJoin[{refDir, name}];
   Get[FileNameJoin[{dir, "inputs.m"}]];                      (* seclist, holdings, subportfolio, settledate *)
   xx = reportFunction1[seclist, holdings, settledate];
   yy = volbySubPortfolio[seclist, holdings, settledate, subportfolio];
   out = {
     "holdings" -> cleanTable[holdingsTable[seclist, holdings, subportfolio]],
     "table1" -> cleanTable[First[displayRF[seclist, holdings, settledate]]],
     "category" -> cleanTable[xx[[1]]],
     "top_contributors" -> cleanTable[xx[[2]]],
     "single_hedge" -> cleanTable[xx[[3]]],
     "best_hedges" -> cleanTable[xx[[4]]],
     "replicating" -> cleanTable[xx[[5]]],
     "subportfolio" -> cleanTable[yy],
     "var" -> cleanTable[varsumm[seclist, holdings, settledate]]};
   Export[FileNameJoin[{dir, "tables.json"}], out, "JSON"];
   Print["Saved ", FileNameJoin[{dir, "tables.json"}]];
   ];



runScenario["scenario1", FileNameJoin[{mmaDir, "SamplePort2.m"}]];
runScenario["scenario2", FileNameJoin[{refDir, "scenario2", "SamplePort2_scenario2.m"}]];
runScenario["scenario3", FileNameJoin[{mmaDir, "SamplePort2.m"}]];

(* ---- Function-level values for the unit tests (original portfolio) ---- *)
loadCode[FileNameJoin[{mmaDir, "SamplePort2.m"}]];
Get[FileNameJoin[{refDir, "original", "inputs.m"}]];
Module[{sec, port, eqv, ext, rep, unit},
  sec = populateSecDV01s[seclist, holdings, settledate];
  port = populatePortDV01s[seclist, holdings, settledate];
  eqv = populateEqvDV01s[seclist, settledate];
  ext = portVolbyVCVextended[seclist, holdings, settledate];
  rep = bestReplicatePort[ext[[12]], ext[[13]], ext[[8]], ext[[9]]];
  unit = {
    "serialday_settle" -> serialday[settledate],
    "pv_example" -> N[pv[0.02, 10, 3, 100]],
    "bondprc_10yrUST" -> N[bondprc[0.0253, settledate, secParmValues[[2]]]],
    "bondoptionprc" -> N[bondoptionprc[0.5, 0.005, 0.0178, 0.0168, 0.2, 5, 2, "C"]],
    "pvPort" -> N[pvPort[seclist, holdings, settledate, marketDataValues]],
    "secDV01s" -> N[sec[[3]]],
    "portDV01Names" -> port[[1]], "portDV01s" -> N[port[[2]]],
    "eqvDV01Names" -> eqv[[1]], "eqvDV01s" -> N[eqv[[2]]],
    "vcv" -> N[populateVCV[port[[1]]]],
    "secVols" -> N[secVolbyVCV[seclist, holdings, settledate][[2]]],
    "rfVols" -> N[rfVolbyVCV[seclist, holdings, settledate][[2]]],
    "portvol" -> N[ext[[1]]], "mcl" -> N[ext[[2]]], "mcp" -> N[ext[[3]]],
    "contallornot" -> N[ext[[4]]], "besthedge" -> N[ext[[5]]], "volbesthedge" -> N[ext[[6]]],
    "corr" -> N[ext[[10]]], "repport" -> N[ext[[11]]],
    "replicate_vols" -> N[rep[[2]]], "replicate_pctvar" -> N[rep[[3]]],
    "replicate_names" -> rep[[5]], "replicate_amounts" -> N[rep[[7]]],
    "mix_pdf" -> N[pdf[normalmix[1.], -2.]],
    "mix_cdf" -> N[cdf[normalmix[1.], -2.]],
    "mix_quantile" -> N[quantile[normalmix[1.], 0.01]],
    "var_normal" -> N[var[normal, 1/255, 1.]],
    "var_student" -> N[var[student, 1/255, 1.]],
    "var_normalmix" -> N[var[normalmix, 1/255, 1.]]};
  Export[FileNameJoin[{refDir, "unit_values.json"}], unit, "JSON"];
  Print["Saved ", FileNameJoin[{refDir, "unit_values.json"}]];
  ];
