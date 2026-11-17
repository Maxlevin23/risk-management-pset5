---
title: "Problem 5: AI Appendix and Contribution Statement"
subtitle: "PPHA 42525 Risk Management, Autumn 2026 (not counted in the 2-page report)"
geometry: "margin=1.8cm"
fontsize: 10pt
mainfont: "Helvetica Neue"
monofont: "Menlo"
monofontoptions: "Scale=0.8"
---

## Tool

Claude Code (Anthropic), working directly in the project folder with the three Mathematica source files and the assignment PDF. It read the files, wrote the code, and ran it; it could not run Mathematica.

## Final prompts

**System prompt (revised from Problem 2).** The Problem 2 prompt was kept and changed in four places for this task: SciPy stays disallowed, so the Student-t and mixture quantiles must be written out; functions take the static data as an argument instead of reading globals; every docstring must name the Mathematica function it translates; and computation must be separated from formatting.

> You are an expert software engineer with deep experience in quantitative finance and risk management. You translate legacy Mathematica code into clean, correct Python. Target: Python 3 with numpy, pandas and the standard library only. Write plain functions, descriptive names, no global variables inside functions (pass the SamplePort2 data in as an argument), no function that modifies its inputs, about 40 lines per function. Every docstring names the Mathematica function it translates and states arguments, units, return value and exceptions. Report functions return raw, unrounded numbers; a separate layer does all rounding and layout. Preserve the original logic, including its quirks, and flag every place where Mathematica's behaviour is ambiguous instead of guessing silently. If a check cannot be satisfied, say so rather than changing the check.

**Part I (structure).**

> Here are `Tables_Ch10.nb`, `DistFn1.m` and `SamplePort2.m`. For each of the nine outputs listed in the assignment, trace which notebook function produces it, which `DistFn1.m` functions that calls, and which `SamplePort2.m` lists those read. Then list every quirk a naive translation would mishandle. Explain specifically why the holdings display shows 9 of 11 positions. Quote the line of code behind each claim so I can check it.

**Part II (translate `DistFn1.m`).**

> Translate every `DistFn1.m` function needed for the nine outputs into `src/distfn.py`, following the system prompt. Here are `SamplePort2.m` and my Problem 2 Python so you can see how the lists are used. Positions must be identified by their place in `seclist`, never by security name, because "10yr UST" appears twice. Translate the custom mixture `pdf`/`cdf`/`quantile` rather than calling a library. List the functions you did not translate and why.

**Part III (tables).**

> Translate the notebook into a script, `src/tables_ch10.py`, that calls the Part II functions. All portfolio inputs live in one file, `src/inputs.py`. Reproduce the notebook's row and column layout and its `NumberForm`/`AccountingForm` rounding, including the switch to scientific notation. Save raw CSVs and formatted tables. Production code must never read `reference/`.

**Part IV (tests and verification).**

> Design scenarios that exercise the Known Pitfalls. Write `verify.py` to run every scenario, compare each output cell by cell with `reference/`, apply the one-unit-in-the-last-digit rule, print a summary and write a side-by-side HTML report with mismatches highlighted. Write unit tests for PVs and DV01s, the VCV and volatilities, contributions and correlations, best-hedge and replicating routines, and the mixture CDF and inverse CDF. Do not report anything as verified that was not actually compared.

## What the AI got wrong, and how it was caught

1. **Double rounding in the display layer.** The first `NumberForm` translation rounded to *n* significant figures and then to *f* decimals. For the CAC index volatility 0.025365051 that gives 0.025365 and then 0.02536; Mathematica shows 0.02537. Caught by comparing the first full run with the notebook PDF, cell by cell. Fixed by rounding once, to the coarser of the two precisions.
2. **A value on a rounding boundary.** Two DV01s are exactly 6,500,000 and display with one digit. The first version showed both as `6×10^6`; after fix 1 both show `7×10^6`; Mathematica shows one of each. Investigation showed the digit is decided by floating-point noise near 1e-8, so this is reported as a known one-unit discrepancy instead of being forced.
3. **Corrupted extraction of the notebook code.** Pulling the table functions out of the `.nb` file's box format, the first attempt mis-detected where `tableContributers` ended and copied 60 lines of unrelated text and a duplicate of `reportFunction1` into the `.wl` file. Caught by listing every definition in the output file and by a bracket-balance check.
4. **Test file that could not be imported.** The first test runner imported the code under test before adding `src/` to the path. Caught immediately by running it.
5. **Something a reader could easily miss: the VaR mixture parameters.** `DistFn1.m` sets alpha = 0.05 and beta = 3; the notebook's `varsumm` quietly uses alpha = 0.01 and beta = 5. The AI flagged this while reading the notebook; it was confirmed by hand (0.99·Φ(−3.0325) + 0.01·Φ(−0.6065) = 1/255 at the displayed 1,680,000).
6. **A limit, not an error.** The AI had no Mathematica kernel, so it could not produce the scenario references or full-precision function values. It wrote the export script and marked those comparisons NO REFERENCE and SKIPPED instead of reporting them as passing. The Mathematica scripts themselves are untested until they are run.

## How the AI's explanation was checked against the code

The Part I claims were checked against the source lines, not taken on trust: `n = 9` and `i < Length[seclist]` in the display cell; `Pick[marketDataValues, ...]` inside `eqtyFutpv`; `alpha = 0.01; beta = 5` inside `varsumm`; `Sign[riskFactorBumpUnit]` in `populateVCV`. Hand calculations confirmed the numbers: CAC exposure (7 + 0.7 × 5) × 1.3 = EUR 10.5mn equivalent, 13.65mn × 0.025365 = 346,200; normal VaR 616,900 × (−2.658) = −1,640,000.

## Contribution statement

*[To be completed by the group: one or two sentences on what each member did.]*
