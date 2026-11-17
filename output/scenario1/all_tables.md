# Tables_Ch10 in Python: scenario1

## 1. Holdings table

Notebook source: `Out[38]`

| Security | Amount (mn local) | Curr | Subportfolio |
| --- | --- | --- | --- |
| 10yr UST | 20 | $ | Government |
| 5yr Bond Opt | -20 | $ | Government |
| 10yr UST | 30 | $ | Swaps |
| 10yr Swap | -20 | $ | Swaps |
| 10yr UKG | -25 | £ | Government |
| FTE CDS | 55 | £ | Credit |
| CAC Index Futures | 7 | € | Equity |
| FTE Equity | 5 | € | Equity |
| GBPCash | -10 | £ | Credit |
| EURCash | 15 | € | Equity |
| 5yr UST | 40 | $ | Government |

## 2. Table 1: Securities, risk factors, DV01s

Notebook source: `displayRF`

| Security | Notional | Security Vol | RIsk Factor | DV01 | DV01 units | RF unit Vol | RF pos'n Vol |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10yr UST | $20mn | 130,800 |  |  |  |  |  |
|  |  |  | USDYld10yr | 18,292 | level | 7.148 | 130,800 |
| 5yr Bond Opt | $-20mn | 20,170 |  |  |  |  |  |
|  |  |  | USDYld5yr | -3,029 | level | 7.073 | 21,430 |
|  |  |  | US5yrOptionVol | -4,254 | level | 2.040 | 8,678 |
| 10yr UST | $30mn | 196,100 |  |  |  |  |  |
|  |  |  | USDYld10yr | 27,438 | level | 7.148 | 196,100 |
| 10yr Swap | $-20mn | 136,500 |  |  |  |  |  |
|  |  |  | USDYld10yr | -17,339 | level | 7.148 | 123,900 |
|  |  |  | USDSwapSp10yr | -17,339 | level | 2.235 | 38,760 |
| 10yr UKG | £-25mn | 400,700 |  |  |  |  |  |
|  |  |  | GBPYld10yr | -28,555 | level | 6.570 | 187,600 |
|  |  |  | GBPFX | -4×10^7 | percent | 0.00811 | 318,200 |
| FTE CDS | £55mn | 65,540 |  |  |  |  |  |
|  |  |  | GBPYld5yr | -79 | level | 6.916 | 548 |
|  |  |  | GBPCredSprd5yr | 33,853 | level | 1.926 | 65,190 |
|  |  |  | GBPFX | -305,390 | percent | 0.00811 | 2,477 |
| CAC Index Futures | €7mn | 230,800 |  |  |  |  |  |
|  |  |  | CACEqIndex | 9×10^6 | percent | 0.02537 | 230,800 |
| FTE Equity | €5mn | 168,900 |  |  |  |  |  |
|  |  |  | CACEqIndex | 5×10^6 | percent | 0.02537 | 115,400 |
|  |  |  | FTEEqSpecific | 7×10^6 | percent | 0.02840 | 184,600 |
|  |  |  | EURFX | 7×10^6 | percent | 0.00791 | 51,410 |
| GBPCash | £-10mn | 113,500 |  |  |  |  |  |
|  |  |  | GBPFX | -1×10^7 | percent | 0.00811 | 113,500 |
| EURCash | €15mn | 154,200 |  |  |  |  |  |
|  |  |  | EURFX | 2×10^7 | percent | 0.00791 | 154,200 |
| 5yr UST | $40mn | 136,200 |  |  |  |  |  |
|  |  |  | USDYld5yr | 19,259 | level | 7.073 | 136,200 |

## 3. Risk-category summary

Notebook source: `reportFunction1[[1]]`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 512,100 | 100.0 | with portfolio |
| FI - rates | 216,500 | 19.6 | 0.463 |
| FI - swap spreads | 38,760 | -1.1 | -0.144 |
| Credit | 65,190 | 6.0 | 0.474 |
| Equity | 296,400 | 33.6 | 0.581 |
| Commodity | 0 | 0 |  |
| FX | 354,600 | 41.4 | 0.597 |
| Volatility | 8,678 | 0.5 | 0.286 |

## 4. Top three contributors

Notebook source: `reportFunction1[[2]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 434,200 | 41.9 | -38.2 | 22.3 | 13.0 | 6.1 |
| CACEqIndex | 346,200 | 33.0 | 10.5 | -7.6 | 12.7 | 10.7 |
| USDYld10yr | 202,900 | 13.0 | 31.0 | -25.7 | 5.5 | 5.3 |

## 5. Best single hedge

Notebook source: `reportFunction1[[3]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| USDSwapSp10yr | 38,760 | -1.1 | -20.0 | -38.1 | 1.0 | -1.4 |

## 6. Top three best hedges

Notebook source: `reportFunction1[[4]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 434,200 | 41.9 | -38.2 | 22.3 | 13.0 | 6.1 |
| CACEqIndex | 346,200 | 33.0 | 10.5 | -7.6 | 12.7 | 10.7 |
| GBPCredSprd5yr | 65,190 | 6.0 | 55.0 | -204.9 | 12.0 | 5.4 |

## 7. Best replicating portfolios

Notebook source: `reportFunction1[[5]]`

|  | One Asset |  | Three Assets |  | Five Assets |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | % Var | % Vol | % Var | % Vol | % Var | % Vol |
| %Var / %Vol Explained | 24.4 | 13.0 | 77.0 | 52.0 | 92.9 | 73.3 |
|  | Asset | Eqv Pos'n | Asset | Eqv Pos'n | Asset | Eqv Pos'n |
| Asset / Eqv Pos'n | GBPFX | -22.3 | GBPFX | -30.7 | GBPFX | -41.5 |
|  |  |  | CACEqIndex | 13.6 | CACEqIndex | 11.6 |
|  |  |  | FTEEqSpecific | 5.6 | FTEEqSpecific | 5.7 |
|  |  |  |  |  | EURFX | 19.7 |
|  |  |  |  |  | USDYld5yr | 47.5 |

## 8. Volatility by subportfolio

Notebook source: `volbySubPortfolio`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 512,100 | 100.0 | with portfolio |
| Credit | 137,500 | 17.2 | 0.642 |
| Equity | 397,200 | 33.1 | 0.427 |
| Government | 370,100 | 46.1 | 0.638 |
| Swaps | 75,350 | 3.5 | 0.240 |

## 9. VaR summary

Notebook source: `varsumm`

| VOLATILITY and 1-ot-of 255 VaR |  |
| --- | --- |
| Volatility | 512,100 |
| VaR Normal | (1,361,000) |
| VaR Student-t (6df) | (1,637,000) |
| VaR Normal Mix (α=1% β=5) | (1,394,000) |
| VaR 4-sigma rule-of-thumb | (2,048,000) |
