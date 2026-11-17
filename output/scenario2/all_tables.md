# Tables_Ch10 in Python: scenario2

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
| 10yr UST | $20mn | 118,800 |  |  |  |  |  |
|  |  |  | USDYld10yr | 16,621 | level | 7.148 | 118,800 |
| 5yr Bond Opt | $-20mn | 20,170 |  |  |  |  |  |
|  |  |  | USDYld5yr | -3,029 | level | 7.073 | 21,430 |
|  |  |  | US5yrOptionVol | -4,254 | level | 2.040 | 8,678 |
| 10yr UST | $30mn | 178,200 |  |  |  |  |  |
|  |  |  | USDYld10yr | 24,932 | level | 7.148 | 178,200 |
| 10yr Swap | $-20mn | 123,700 |  |  |  |  |  |
|  |  |  | USDYld10yr | -15,710 | level | 7.148 | 112,300 |
|  |  |  | USDSwapSp10yr | -15,710 | level | 2.235 | 35,110 |
| 10yr UKG | £-25mn | 457,900 |  |  |  |  |  |
|  |  |  | GBPYld10yr | -32,634 | level | 6.570 | 214,400 |
|  |  |  | GBPFX | -4×10^7 | percent | 0.00811 | 363,600 |
| FTE CDS | £55mn | 74,900 |  |  |  |  |  |
|  |  |  | GBPYld5yr | -90 | level | 6.916 | 626 |
|  |  |  | GBPCredSprd5yr | 38,689 | level | 1.926 | 74,500 |
|  |  |  | GBPFX | -349,010 | percent | 0.00811 | 2,831 |
| CAC Index Futures | €7mn | 230,800 |  |  |  |  |  |
|  |  |  | CACEqIndex | 9×10^6 | percent | 0.02537 | 230,800 |
| FTE Equity | €5mn | 168,900 |  |  |  |  |  |
|  |  |  | CACEqIndex | 5×10^6 | percent | 0.02537 | 115,400 |
|  |  |  | FTEEqSpecific | 7×10^6 | percent | 0.02840 | 184,600 |
|  |  |  | EURFX | 6×10^6 | percent | 0.00791 | 51,410 |
| GBPCash | £-10mn | 129,800 |  |  |  |  |  |
|  |  |  | GBPFX | -2×10^7 | percent | 0.00811 | 129,800 |
| EURCash | €15mn | 154,200 |  |  |  |  |  |
|  |  |  | EURFX | 2×10^7 | percent | 0.00791 | 154,200 |
| 5yr UST | $40mn | 136,200 |  |  |  |  |  |
|  |  |  | USDYld5yr | 19,259 | level | 7.073 | 136,200 |

## 3. Risk-category summary

Notebook source: `reportFunction1[[1]]`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 546,300 | 100.0 | with portfolio |
| FI - rates | 201,500 | 15.7 | 0.425 |
| FI - swap spreads | 35,110 | -0.9 | -0.134 |
| Credit | 74,500 | 6.5 | 0.475 |
| Equity | 296,400 | 27.6 | 0.509 |
| Commodity | 0 | 0 |  |
| FX | 410,400 | 50.8 | 0.676 |
| Volatility | 8,678 | 0.3 | 0.219 |

## 4. Top three contributors

Notebook source: `reportFunction1[[2]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 496,200 | 53.6 | -38.2 | 24.8 | 19.3 | 13.2 |
| CACEqIndex | 346,200 | 26.3 | 10.5 | -6.9 | 9.0 | 6.4 |
| USDYld10yr | 184,700 | 7.7 | 31.1 | -21.1 | 2.7 | 2.1 |

## 5. Best single hedge

Notebook source: `reportFunction1[[3]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| EURFX | 205,600 | -2.8 | 20.0 | 4.0 | 0.3 | -9.5 |

## 6. Top three best hedges

Notebook source: `reportFunction1[[4]]`

|  | Exp Vol |  | Curr Pos'n | Trade to best | % Reduction in Vol to |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | (1-sig P&L) | Contribution | (mn eqv) | Hedge (eqv) | Best Hedge | Zero Pos'n |
| GBPFX | 496,200 | 53.6 | -38.2 | 24.8 | 19.3 | 13.2 |
| GBPCredSprd5yr | 74,500 | 6.5 | 55.0 | -191.8 | 12.0 | 5.7 |
| CACEqIndex | 346,200 | 26.3 | 10.5 | -6.9 | 9.0 | 6.4 |

## 7. Best replicating portfolios

Notebook source: `reportFunction1[[5]]`

|  | One Asset |  | Three Assets |  | Five Assets |  |
| --- | --- | --- | --- | --- | --- | --- |
|  | % Var | % Vol | % Var | % Vol | % Var | % Vol |
| %Var / %Vol Explained | 34.8 | 19.3 | 80.2 | 55.5 | 92.1 | 71.9 |
|  | Asset | Eqv Pos'n | Asset | Eqv Pos'n | Asset | Eqv Pos'n |
| Asset / Eqv Pos'n | GBPFX | -24.8 | GBPFX | -32.2 | GBPFX | -41.6 |
|  |  |  | CACEqIndex | 13.5 | CACEqIndex | 11.8 |
|  |  |  | FTEEqSpecific | 5.7 | FTEEqSpecific | 5.8 |
|  |  |  |  |  | EURFX | 20.1 |
|  |  |  |  |  | USDYld5yr | 37.6 |

## 8. Volatility by subportfolio

Notebook source: `volbySubPortfolio`

|  | Exp Vol ($) | Contribution | Correlation |
| --- | --- | --- | --- |
| Overall | 546,300 | 100.0 | with portfolio |
| Credit | 157,100 | 20.8 | 0.724 |
| Equity | 397,200 | 24.8 | 0.341 |
| Government | 416,400 | 52.5 | 0.689 |
| Swaps | 68,710 | 1.9 | 0.151 |

## 9. VaR summary

Notebook source: `varsumm`

| VOLATILITY and 1-ot-of 255 VaR |  |
| --- | --- |
| Volatility | 546,300 |
| VaR Normal | (1,453,000) |
| VaR Student-t (6df) | (1,747,000) |
| VaR Normal Mix (α=1% β=5) | (1,488,000) |
| VaR 4-sigma rule-of-thumb | (2,185,000) |
