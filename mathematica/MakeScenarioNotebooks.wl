(* ::Package:: *)

(* MakeScenarioNotebooks.wl
   Reruns the Tables_Ch10 reports for each test scenario and saves, per scenario,
     reference/<scenario>/Tables_Ch10_<scenario>.nb    the rerun notebook (inputs + outputs)
     reference/<scenario>/Tables_Ch10_<scenario>.pdf   the same notebook printed to PDF

   Each notebook contains the changed input lines (reference/<scenario>/inputs.m)
   and the nine outputs exactly as the original notebook draws them:
   displayRF, Grid[reportFunction1[...][[1..5]], Frame -> All],
   Grid[volbySubPortfolio[...], Frame -> All] and Grid[varsumm[...], Frame -> All].
   The holdings table shows every position (the original display stops at 9).

   Run from the project folder:  wolframscript -file mathematica/MakeScenarioNotebooks.wl
   Needs a front end for the PDF export (desktop Mathematica or Wolfram Cloud). *)

mmaDir = DirectoryName[$InputFileName];
If[mmaDir === "", mmaDir = NotebookDirectory[]];
refDir = FileNameJoin[{ParentDirectory[mmaDir], "reference"}];

loadCode[sampleFile_] := (
   Get[sampleFile];
   Get[FileNameJoin[{mmaDir, "DistFn1.m"}]];
   Get[FileNameJoin[{mmaDir, "TableFunctions.wl"}]];);

holdingsGrid[] := Grid[Join[{{"Security", "Amount (mn local)", "Curr", "Subportfolio"}},
    Table[{seclist[[i]], holdings[[i]],
      fxsymb[seclist[[i]], {"$", "\[Yen]", "\[Sterling]", "\[Euro]"}, {"USD", "JPY", "GBP", "EUR"}][[1]],
      subportfolio[[i]]}, {i, Length[seclist]}]], Frame -> All];

section[title_, expr_] := {Cell[title, "Subsection"], Cell[BoxData[ToBoxes[expr]], "Output"]};

scenarioNotebook[name_, sampleFile_] := Module[{inputsFile, xx, yy},
   loadCode[sampleFile];
   inputsFile = FileNameJoin[{refDir, name, "inputs.m"}];
   Get[inputsFile];
   xx = reportFunction1[seclist, holdings, settledate];
   yy = volbySubPortfolio[seclist, holdings, settledate, subportfolio];
   Notebook[Flatten[{
      Cell["Tables_Ch10 \[LongDash] " <> name, "Title"],
      Cell["Rerun of the Tables_Ch10.nb reports with SamplePort2.m, DistFn1.m and the notebook's table functions. " <>
        "Market data file: " <> FileNameTake[sampleFile] <> ". Kernel: " <> $Version <> ".", "Text"],
      Cell["Changed inputs (" <> FileNameTake[inputsFile] <> ")", "Subsection"],
      Cell[Import[inputsFile, "Text"], "Program"],
      section["1. Holdings (all positions)", holdingsGrid[]],
      section["2. Table 1 \[LongDash] displayRF[seclist, holdings, settledate]", displayRF[seclist, holdings, settledate]],
      section["3. Grid[xx[[1]]] \[LongDash] risk-category summary", Grid[xx[[1]], Frame -> All]],
      section["4. Grid[xx[[2]]] \[LongDash] top three contributors", Grid[xx[[2]], Frame -> All]],
      section["5. Grid[xx[[3]]] \[LongDash] best single hedge", Grid[xx[[3]], Frame -> All]],
      section["6. Grid[xx[[4]]] \[LongDash] top three best hedges", Grid[xx[[4]], Frame -> All]],
      section["7. Grid[xx[[5]]] \[LongDash] best replicating portfolios", Grid[xx[[5]], Frame -> All]],
      section["8. Grid[yy] \[LongDash] volatility by subportfolio", Grid[yy, Frame -> All]],
      section["9. Grid[varsumm[...]] \[LongDash] VaR summary", Grid[varsumm[seclist, holdings, settledate], Frame -> All]]
      }]]
   ];

saveScenario[name_, sampleFile_] := Module[{nb, base},
   nb = scenarioNotebook[name, sampleFile];
   base = FileNameJoin[{refDir, name, "Tables_Ch10_" <> name}];
   Export[base <> ".nb", nb];
   Export[base <> ".pdf", nb];
   Print["Saved ", base, ".nb and .pdf"];
   ];

saveScenario["scenario1", FileNameJoin[{mmaDir, "SamplePort2.m"}]];
saveScenario["scenario2", FileNameJoin[{refDir, "scenario2", "SamplePort2_scenario2.m"}]];
saveScenario["scenario3", FileNameJoin[{mmaDir, "SamplePort2.m"}]];
