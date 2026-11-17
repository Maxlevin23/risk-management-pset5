(* ::Package:: *)

(* TableFunctions.wl
   The table/report functions of Tables_Ch10.nb, copied out of the notebook's
   Input cells as plain text so that a script can load them (see RunScenarios.wl).
   The code is unchanged; only the notebook's special operator characters
   (rule arrow, <=, ==, !=) are written in plain ASCII.
   Requires SamplePort2.m and DistFn1.m to be loaded first. *)


tableContributers[ordering_,rflist_,portvol_,volexplained_,combvol_,nav_]:=Module[{xx2,xx3,k},
k = Length[ordering];
xx2 = {{"", "Exp Vol", "", "Curr Pos'n", "Trade to best", "% Reduction in Vol to", SpanFromLeft},
   {"", "(1-sig P&L)", "Contribution", "(mn eqv)", "Hedge (eqv)", "Best Hedge", "Zero Pos'n"}};
xx3 = Join[xx2, Table[{rflist[[ordering[[i]]]],
     If[nav>1,
NumberForm[100*portvol[[7]][[ordering[[i]]]]/nav, {5, 4}], (* RF vol in percentage *)
AccountingForm[portvol[[7]][[ordering[[i]]]], {4, 0}, DigitBlock -> 3, NumberPoint -> ""]], (* RF vol *)
     NumberForm[100*portvol[[3]][[ordering[[i]]]], {4, 1}], (* Cont'n *)
     NumberForm[(portvol[[5]][[ordering[[i]]]] + portvol[[11]][[ordering[[i]]]]), {4, 1}], (* Original pos'n *)
     NumberForm[-portvol[[11]][[ordering[[i]]]], {4, 1}], (* Trade to best hedge *)
     NumberForm[volexplained[[ordering[[i]]]], {4, 1}], (* Vol explained % *)
     NumberForm[100*portvol[[4]][[ordering[[i]]]]/combvol, {4, 1}](* Vol explained % *)},
    {i, 1, k}]]
]


reportFunction1[seclist_,holdings_,settledate_,nav_] := Module[{xx,portvol,yy,x,y,combvol,i,table,rflist,xx2,xx3,xx4,xx5,xx6,zz,volexplained,ordering,replicateport},
portvol = portVolbyVCVextended[seclist,holdings,settledate];
(* 
1. portfolio volatility
2. list of marginal contributions (vector) in levels (for risk factors)
3. marginal contributions proportional
4. All-or-nothing contribution (change in vol when this pos'n is set to zero)
5. Best hedge position (in same units as inputholdingsItalic)-must fix because by RFs not securities
6. Volatility at best hedge
7. Stand-alone volatilities of individual risk factors
8. RF list (remember that although seclistItalic Italicis input,risk is done by RFs
9. DV01s by RFs per 1 unit holdings
10. Correlations of RFs with portfolio
11. Replicating position (=original-best hedge) 
12. DV01s by RFs (actual holdings)
13. VCV matrix   *)
combvol=portvol[[1]];
rflist = portvol[[8]];
volexplained = 100.0*(1 - portvol[[6]]/combvol);
yy={"FI - rates","FI - swap spreads","Credit","Equity","Commodity","FX","Volatility"}; (* List of headings - RFs are labeled by these *)
xx =Flatten[ Table[Pick[riskFactorCategory,riskFactorNames,rflist[[i]]],{i,1,Length[rflist]}]]; (* This is a list, in same order as rflist, of headings *)
zz=ConstantArray[0,Length[yy]]; (* Empty list into which vols will be insterted *)
For[i=1,i<=Length[yy],i++, (* Calculate vol by category *)
xx4 = ConstantArray[0,Length[xx]];
xx3=Flatten[Position[xx,yy[[i]]]];
xx4[[xx3]]=portvol[[12]][[xx3]]; (* DV01s for this category *)
zz[[i]]=Sqrt[xx4.portvol[[13]].xx4]; (* vol for this category *)
];
If[nav>1,
xx2=Table[{yy[[i]],NumberForm[100*zz[[i]]/nav,{5,4}],NumberForm[100*(x=Total[Pick[portvol[[3]],xx,yy[[i]]]]),{4,1}],If[zz[[i]]>0,NumberForm[x*combvol/zz[[i]],{4,3}],""]},{i,1,Length[yy]}];
table = {{"","Exp Vol (%)","Contribution","Correlation"},
{"Overall",NumberForm[100*combvol/nav,{5,4}],"100.0","with portfolio"}};,
xx2=Table[{yy[[i]],AccountingForm[zz[[i]],{4,0},DigitBlock->3,NumberPoint->""],NumberForm[100*(x=Total[Pick[portvol[[3]],xx,yy[[i]]]]),{4,1}],If[zz[[i]]>0,NumberForm[x*combvol/zz[[i]],{4,3}],""]},{i,1,Length[yy]}];
table = {{"","Exp Vol ($)","Contribution","Correlation"},
{"Overall",AccountingForm[combvol,{4,0},DigitBlock->3,NumberPoint->""],"100.0","with portfolio"}};
];
table=Join[table,xx2];
ordering = Ordering[-portvol[[3]],3]; (* top 5 contributers to vol *)
xx3=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
ordering = Ordering[portvol[[3]],1]; (* top 3 neg contributers to vol *)
xx4=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
ordering = Ordering[portvol[[6]],3]; (* top 5 best single hedges *)
xx5=tableContributers[ordering,rflist,portvol,volexplained,combvol,nav];
(* Now format the "Replicating Portfolio" table *)
replicateport=bestReplicatePort[portvol[[12]],portvol[[13]],portvol[[8]],portvol[[9]]];
xx6={{"","One Asset",SpanFromLeft,"Three Assets",SpanFromLeft,"Five Assets",SpanFromLeft},{"","% Var","% Vol","% Var","% Vol","% Var","% Vol"},
Join[{"%Var / %Vol Explained"},Flatten[Table[{NumberForm[100*replicateport[[3,i]],{4,1}],NumberForm[100*replicateport[[4,i]],{4,1}]},{i,{1,3,5}}]]],
{"","Asset","Eqv Pos'n","Asset","Eqv Pos'n","Asset","Eqv Pos'n"},
Join[{"Asset / Eqv Pos'n"},Flatten[Table[{replicateport[[5,1]],NumberForm[replicateport[[7,i,1]],{4,1}]},{i,{1,3,5}}]]],
Join[{"","",""},Flatten[Table[{replicateport[[5,2]],NumberForm[replicateport[[7,i,2]],{4,1}]},{i,{3,5}}]]],Join[{"","",""},Flatten[Table[{replicateport[[5,3]],NumberForm[replicateport[[7,i,3]],{4,1}]},{i,{3,5}}]]],
{"","","","","",replicateport[[5,4]],NumberForm[replicateport[[7,5,4]],{4,1}]},
{"","","","","",replicateport[[5,5]],NumberForm[replicateport[[7,5,5]],{4,1}]}
};

table = {table,xx3,xx4,xx5,xx6}
]


reportFunction1[seclist_, holdings_, settledate_] :=reportFunction1[seclist,holdings,settledate,1]


volbySubPortfolio[seclist_,holdings_,settledate_,subportfolio_]:=Module[{x1,x2,x3,x4,subportlist,noclass,results,i,j,xhold,table,partial,zeros},
subportlist=Union[subportfolio];    (* List of unique asset classes *)
noclass=Length[subportlist];          (* Number of asset classes *)
zeros=ConstantArray[0,Length[holdings]];  (* used for holding subportfolio holdings *)
results =  portVolbyVCVextended[seclist,holdings,settledate];  (* for complete portfolio *)
For[i=1,i<=noclass,i++,
x1=Flatten[Position[subportfolio,subportlist[[i]]]];   (* indexes of this asset class in seclist *)
xhold = zeros;xhold[[x1]]=holdings[[x1]];  (* insert holdings for this subportfolio *)
x2 = portVolbyVCVextended[seclist,xhold,settledate];
results = Join[results,x2];  (* This stacks additional results onto the end - each "results" is 13 long, so two stacked is 26, 3 is 39, ... *)
];
partial = results[[13]].results[[12]]; (* Matrix multiplication of VCV . Delta *)
table={{"","Exp Vol ($)","Contribution","Correlation"},
{"Overall",AccountingForm[x1=results[[1]],{4,0},DigitBlock->3,NumberPoint->""],"100.0","with portfolio"}};
table = Join[table,
Table[{subportlist[[i]],AccountingForm[x2=results[[13*i+1]],{4,0},DigitBlock->3,NumberPoint->""],NumberForm[x3=100*(results[[13*i+12]].partial)/(x1^2),{4,1}],If[x2>0,NumberForm[x3*x1/(100*x2),{4,3}],""]},{i,1,noclass}]]
]


varsumm[seclist_,holdings_,settledate_]:=Module[{x1,x2,alpha,beta,mixfact,normalmix},
x1=portVolbyVCV[seclist,holdings,settledate];
alpha=0.01;beta=5;mixfact = Sqrt[1-alpha + alpha*beta*beta];
normalmix[vol_]:=MixtureDistribution[{1-alpha,alpha},{NormalDistribution[0,vol/mixfact],NormalDistribution[0,beta*vol/mixfact]}];
x2 = {{"VOLATILITY and 1-ot-of 255 VaR",SpanFromLeft},
{"Volatility",AccountingForm[x1,{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Normal",AccountingForm[Quantile[NormalDistribution[0,x1],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Student-t (6df)",AccountingForm[x1*Sqrt[4/6]*Quantile[StudentTDistribution[6],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR Normal Mix (\[Alpha]=1% \[Beta]=5)",AccountingForm[Quantile[normalmix[x1],1/255],{4,0},DigitBlock->3,NumberPoint->""]},
{"VaR 4-sigma rule-of-thumb",AccountingForm[-4*x1,{4,0},DigitBlock->3,NumberPoint->""]}}
]


displayRF[seclist_,holdings_,settledate_] := Module[{x,xx,y,z,secDV01s,outTable,i,j,symb,isocode,vcv,secVols,rfVols},
symb = {"$","\[Yen]","\[Sterling]","\[Euro]"};
isocode = {"USD","JPY","GBP","EUR"};
secDV01s = Transpose[populateSecDV01s[seclist,holdings,settledate]];
secVols = Transpose[secVolbyVCV[seclist,holdings,settledate]];
rfVols = Transpose[rfVolbyVCV[seclist,holdings,settledate]];
outTable={{"Security","Notional","Security Vol","RIsk Factor","DV01","DV01 units","RF unit Vol","RF pos'n Vol"}};
For[i=1,i<=Length[seclist],i++,   (* Loop through securities *)
x = fxsymb[seclist[[i]],symb,isocode];
x = x[[1]]<>ToString[holdings[[i]]]<>"mn";
y =NumberForm[secVols[[i,2]],{4,0},DigitBlock->3,NumberPoint->""];
x = {{Style[seclist[[i]],Bold],x,y,"","","","",""}};
outTable=Join[outTable,x];
For [j=1,j<=Length[secDV01s[[i,2]]],j++,   (* Loop through RFs for each security and figure out RF items *)
x = {{"","","",secDV01s[[i,2,j]],NumberForm[secDV01s[[i,3,j]],{5,0},DigitBlock->3,NumberPoint->""],"","",""}};
y=Pick[riskFactorBumpTypes,riskFactorNames,x[[1,4]]][[1]];  (* Figure out bump type *)
x[[1,6]]=y;      (* put into line *)
z=Pick[marketVols,marketDataNames,x[[1,4]]][[1]];  (* Figure out vol *)
xx =NumberForm[z,If[y=="percent",{5,5},{4,3}]];
x[[1,7]] = xx;     (* insert vol in *)
y =NumberForm[Abs[secDV01s[[i,3,j]]*z],{4,0},DigitBlock->3,NumberPoint->""];
x[[1,8]]=y;          (* insert rf vol for this position *)
outTable = Join[outTable,x];      (* tack on line of RF data *)
];
];
Grid[outTable,Frame->All]
]


bestReplicatePort[delta_,sigma_,rfnames_,rfunitDV01s_] := Module[{x,y,z,part,portvar,dstar,index,portvar5,varchk,i,j,k,portsize,partint,sigmaint,dstarint,varint,dstarint5,nosec,portvarPercent,names,amounts,portvolPercent},
(* The 'inputs' are                                           *)
(*    delta - column vector of deltas or portfolio weights    *)
(*    sigma - variance-covariance matrix sigma                *)
(* The portfolio variance is                                  *)
(*     d' * sigma * d                                         *)
(* We need the following as intermediate                      *)
(*     part = sigma * d - column vector of partial multiplication    *)
(* The variance when the 'best hedges' for i,j,k is           *)
(*     portvar - part[i j k]' * inv(sigma[i j k, i j k]) * part[i j k]  *)
(* so the variance reduction                                 *)
(*     part[i j k]' * inv(sigma[i j k, i j k]) * part[i j k]  *)
(* The coefficients (weights or delta) of the best hedges are *)
(*     dstar = -inv(sigma[i j k]) * part[i j k] + delta[i j k]    *)
(* so we want the intermediate results                        *)
(*     dstar_int = inv(sigma[i j k]) * part[i j k]         *)
(* to get it as                                               *)
(*     dstar_int = part[i j k] / sigma[i j k]              *)
(* and then                                                   *)
(*     var_bh = part[ ]' * dstar_int                       *)
(* and save dstarint, var_bh, and {i,j,k} for later comparison   *)
(*  Output  
1. Overall Port vol
2. Port vol for each replicating
3. Percent por variance explained
4. Percent port volatility explained
5. RF names
6. Ragged array of RF deltas (DV01s)
7. Ragged array of RF amounts (if there are eqvs)  *)
nosec=5;   (* Build replicating portfolios for 1-5 securities *)
portsize=Length[delta];
part=sigma.delta;
portvar=delta.part;
index=ConstantArray[0,nosec];
dstarint5={{}}; (* These will be ragged array of positions, names, etc *)
 names={}; amounts={{}};  
portvar5=ConstantArray[0,nosec];
For[i=1,i<=nosec,i++,
varchk=portvar;
For[j=1,j<=portsize,j++, (* Loop through assets *)
If[MemberQ[index,j],Null,  (* If this asset has not been selected yet then go *)
index[[i]]=j; (* Add this asset's index to the list of selected assets *)
partint=part[[index[[1;;i]]]]; (* Select out appropriate assets *)
sigmaint=sigma[[index[[1;;i]],index[[1;;i]]]];
dstarint=LinearSolve[sigmaint,partint];  (* Intermediate result *)
varint=portvar-partint.dstarint;  (* Variance for this set of assets *)
If[varint<varchk,  (* If lowest so far *)
varchk=varint;
k=j;,                            (* Keep track of index *)
Null;];
];   (* End If for MemberQ *)
];  (* End looping over assets *)
index[[i]]=k;                         (* Now do everything for the best of this loop *)
partint=part[[index[[1;;i]]]];
sigmaint=sigma[[index[[1;;i]],index[[1;;i]]]];
portvar5[[i]]=varchk;
dstarint5=Join[dstarint5,{LinearSolve[sigmaint,partint]}];  (* This is poition at best "best hedge" *)
names=Join[names,{rfnames[[k]]}];
y={};
For[j=1,j<=i,j++,
If[rfunitDV01s[[index[[j]]]] != 0,x=dstarint5[[i+1,j]]/rfunitDV01s[[index[[j]]]],x=0];
y=Join[y,{x}];
];
amounts=Join[amounts,{y}];
];      (* End loop for replicates *)
portvarPercent=1-(portvar5/portvar);   (* Percentage of original portfolio variance explained *)
portvolPercent = 1 - (Sqrt[portvar5]/Sqrt[portvar]); (* Percentage vol explained *)
dstarint5=dstarint5[[2;;6]];  (* Drop off first element (empty) *)
amounts=amounts[[2;;6]];
{Sqrt[portvar],Sqrt[portvar5],portvarPercent,portvolPercent,names,dstarint5,amounts}
]


Off[NumberForm::sigz]
