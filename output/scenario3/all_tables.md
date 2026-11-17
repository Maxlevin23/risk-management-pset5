# Tables_Ch10 in Python: scenario3

## 1. Holdings table

Notebook source: `Out[38]`

| Security | Amount (mn local) | Curr | Subportfolio |
| --- | --- | --- | --- |
| 5yr UST | 35 | $ | Rates |
| 10yr UST | -12.5 | $ | Rates |
| 10yr UST | 12.5 | $ | Macro |
| Swap201901 | -40 | $ | Macro |
| 5yr UKG | 18 | £ | Rates |
| 10yr Bund | -22 | € | Macro |
| 5yr Bund | 30 | € | Rates |
| SPX Index Futures | -9 | $ | Equity |
| FTE Equity | 6 | € | Equity |
| FTE CDS | 25 | £ | Credit |
| EURCash | -8 | € | Macro |
| GBPCash | 0 | £ | Credit |
| 5yr Bond Opt | 10 | $ | Rates |

## 2. Table 1: Securities, risk factors, DV01s

Notebook source: `displayRF`

| Security | Notional | Security Vol | RIsk Factor | DV01 | DV01 units | RF unit Vol | RF pos'n Vol |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5yr UST | $35mn | 108,700 |  |  |  |  |  |
|  |  |  | USDYld5yr | 15,362 | level | 7.073 | 108,700 |
| 10yr UST | $-12.5mn | 78,410 |  |  |  |  |  |
|  |  |  | USDYld10yr | -10,970 | level | 7.148 | 78,410 |
| 10yr UST | $12.5mn | 78,410 |  |  |  |  |  |
|  |  |  | USDYld10yr | 10,970 | level | 7.148 | 78,410 |
| Swap201901 | $-40mn | 260,800 |  |  |  |  |  |
|  |  |  | USDYld10yr | -33,126 | level | 7.148 | 236,800 |
|  |  |  | USDSwapSp10yr | -33,126 | level | 2.235 | 74,040 |
| 5yr UKG | £18mn | 265,200 |  |  |  |  |  |
|  |  |  | GBPYld5yr | 12,640 | level | 6.916 | 87,420 |
|  |  |  | GBPFX | 3×10^7 | percent | 0.00811 | 225,500 |
| 10yr Bund | €-22mn | 307,100 |  |  |  |  |  |
|  |  |  | EURYld10yr | -25,629 | level | 5.735 | 147,000 |
|  |  |  | EURFX | -3×10^7 | percent | 0.00791 | 245,300 |
| 5yr Bund | €30mn | 375,300 |  |  |  |  |  |
|  |  |  | EURYld5yr | 16,564 | level | 6.142 | 101,700 |
|  |  |  | EURFX | 4×10^7 | percent | 0.00791 | 333,600 |
| SPX Index Futures | $-9mn | 139,100 |  |  |  |  |  |
|  |  |  | SPXEqIndex | -9×10^6 | percent | 0.01546 | 139,100 |
| FTE Equity | €6mn | 202,600 |  |  |  |  |  |
|  |  |  | CACEqIndex | 5×10^6 | percent | 0.02537 | 138,500 |
|  |  |  | FTEEqSpecific | 8×10^6 | percent | 0.02840 | 221,500 |
|  |  |  | EURFX | 8×10^6 | percent | 0.00791 | 61,690 |
| FTE CDS | £25mn | 29,790 |  |  |  |  |  |
|  |  |  | GBPYld5yr | -36 | level | 6.916 | 249 |
|  |  |  | GBPCredSprd5yr | 15,388 | level | 1.926 | 29,630 |
|  |  |  | GBPFX | -138,810 | percent | 0.00811 | 1,126 |
| EURCash | €-8mn | 82,250 |  |  |  |  |  |
|  |  |  | EURFX | -1×10^7 | percent | 0.00791 | 82,250 |
| GBPCash | £0mn | 0 |  |  |  |  |  |
|  |  |  | GBPFX | 0 | percent | 0.00811 | 0 |
| 5yr Bond Opt | $10mn | 10,080 |  |  |  |  |  |
|  |  |  | USDYld5yr | 1,515 | level | 7.073 | 10,710 |
|  |  |  | US5yrOptionVol | 2,127 | level | 2.040 | 4,339 |

## 3. Risk-category summary

Notebook source: `reportFunction1[[1]]`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 390,100 | 100.0 | with portfolio |
| FI - rates | 172,500 | 25.7 | 0.582 |
| FI - swap spreads | 74,040 | 4.5 | 0.235 |
| Credit | 29,630 | 1.5 | 0.201 |
| Equity | 204,600 | 24.6 | 0.468 |
| Commodity | 0 | 0 |  |
| FX | 269,800 | 43.7 | 0.631 |
| Volatility | 4,339 | 0.0 | 0.038 |

## 4. Top three contributors

Notebook source: `reportFunction1[[2]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 224,300 | 35.9 | 19.8 | -21.5 | 21.9 | 21.8 |
| USDYld10yr | 236,800 | 26.4 | -37.7 | 27.1 | 10.0 | 8.4 |
| FTEEqSpecific | 221,500 | 25.3 | 6.0 | -4.7 | 10.5 | 9.7 |

## 5. Best single hedge

Notebook source: `reportFunction1[[3]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| USDYld5yr | 119,400 | -9.2 | 38.5 | 37.6 | 4.6 | -13.0 |

## 6. Top three best hedges

Notebook source: `reportFunction1[[4]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 224,300 | 35.9 | 19.8 | -21.5 | 21.9 | 21.8 |
| FTEEqSpecific | 221,500 | 25.3 | 6.0 | -4.7 | 10.5 | 9.7 |
| EURFX | 67,750 | 7.7 | 6.6 | -16.9 | 10.5 | 6.4 |

## 7. Best replicating portfolios

Notebook source: `reportFunction1[[5]]`

|  | One Asset |  | Three Assets |  | Five Assets |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | % Var | % Vol | % Var | % Vol | % Var | % Vol |
| %Var / %Vol Explained | 39.0 | 21.9 | 83.4 | 59.2 | 87.9 | 65.3 |
|  | Asset | Eqv Pos'n | Asset | Eqv Pos'n | Asset | Eqv Pos'n |
| Asset / Eqv Pos'n | GBPFX | 21.5 | GBPFX | 24.2 | GBPFX | 21.4 |
|  |  |  | FTEEqSpecific | 4.9 | FTEEqSpecific | 5.8 |
|  |  |  | USDYld10yr | -27.0 | USDYld10yr | -36.7 |
|  |  |  |  |  | EURYld5yr | 23.7 |
|  |  |  |  |  | CACEqIndex | 2.0 |

## 8. Volatility by subportfolio

Notebook source: `volbySubPortfolio`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 390,100 | 100.0 | with portfolio |
| Credit | 29,790 | 1.3 | 0.176 |
| Equity | 201,200 | 31.6 | 0.613 |
| Macro | 465,500 | -7.5 | -0.063 |
| Rates | 588,800 | 74.6 | 0.494 |

## 9. VaR summary

Notebook source: `varsumm`

| VOLATILITY and 1-ot-of 255 VaR |  |
| --- | --- |
| Volatility | 390,100 |
| VaR Normal | (1,037,000) |
| VaR Student-t (6df) | (1,247,000) |
| VaR Normal Mix (α=1% β=5) | (1,062,000) |
| VaR 4-sigma rule-of-thumb | (1,561,000) |
