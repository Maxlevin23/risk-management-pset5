---
title: "Problem 5: AI Appendix"
subtitle: "PPHA 42525 Risk Management, Autumn 2026 (not counted in the 2-page report)"
geometry: "margin=1.8cm"
fontsize: 10pt
mainfont: "Helvetica Neue"
monofont: "Menlo"
monofontoptions: "Scale=0.8"
---

AI wrote nearly all of this translation, which is exactly why none of it was taken on trust. Translating the 609 lines of `DistFn1.m` and the notebook's table functions was the smaller job; proving the result correct took most of the effort, and surfaced the seven problems listed below, two of which changed displayed numbers. This appendix records the prompts, the mistakes, and how each one surfaced.

## Tool

Claude Code (Anthropic) worked directly in the project folder with the three Mathematica source files and the assignment PDF: it read the files, wrote the code, ran it, and checked the output. Mathematica 15.0.1 was run in Wolfram Cloud through a signed-in browser session, using export scripts the AI wrote.

## Final prompts

The work ran as one agentic session rather than one prompt per part. The prompts below are quoted exactly as typed, spelling included. The assignment PDF was attached to the first, and the AI took each part's requirements (Parts I to IV, the known pitfalls, the deliverables list) directly from it.

**Prompt 1 (Parts I to IV in one request), with `problem5_Q.pdf` attached:**

> heres the latest assignment for risk management, i want you to complete everything outlined by the assignment, output the code in the risk mangement folder, the neatly organized python code, a pdf, doc of the code, the mathematica code with it, the explanations requested as their own document, and then check the code to make sure it matches the tables

**Prompt 2 (packaging and deliverables):**

> now format everything for assignment submission neatly in my risk mangement folder, as well as the pdf output of the code and the explanations that the professor wants submitted

**Prompt 3 (repository and remaining items):**

> push the checkpoint to its own title as risk mangement pset 5 and then finish all the open stuff please

Later short prompts asked the AI to commit and push, to run the Mathematica scenarios once Wolfram Cloud was open in the browser, to produce the rerun scenario notebooks, to package the Part I to IV deliverables, and to rewrite the written sections in a set house style.

**Standing instructions the AI also read.** The Problem 2 system prompt (`Mathematica_to_pythonPrompttemplate.md`) sat in the project folder, and the AI read it before writing any code. Its rules carried over unchanged: numpy, pandas and the standard library only; plain functions with descriptive names; no global variables inside functions; functions of about 40 lines; docstrings stating arguments, units and return values; and preserve the Mathematica logic, flagging ambiguity rather than guessing.

**How the Problem 2 prompt should change for this task.** Four additions describe what the AI did beyond that prompt and belong in it next time: (1) pass the `SamplePort2.m` data into every function as an argument, so a market-data scenario cannot leak into the base data; (2) name, in each docstring, the Mathematica function being translated; (3) have report functions return raw, unrounded numbers and leave all rounding to a separate layer; and (4) identify positions by their place in `seclist`, never by security name, and never report anything as verified that was not actually compared.

## What the AI got wrong, and how it was caught

1. **Double rounding in the display layer.** The first `NumberForm` translation rounded to *n* significant figures and then to *f* decimals, so the CAC index volatility of 0.025365051 became 0.025365 and then 0.02536; Mathematica shows 0.02537. A cell-by-cell comparison with the notebook PDF caught it on the first full run. Rounding once, to the coarser of the two precisions, fixed it.
2. **Dividing where Mathematica multiplies by a reciprocal.** Two FTE Equity DV01s are both 6,500,000 and display with one digit; Mathematica shows `7×10^6` for one and `6×10^6` for the other, while Python showed `7×10^6` for both. The AI first wrote this off as unavoidable floating-point noise. It was not. The full-precision Mathematica export showed the exact values (6,500,000.000000022 and 6,499,999.999999975), and testing each possible operation order showed that Mathematica computes `a*b*x/fx` as (a·b) × (x × fx⁻¹). Written that way, Python now matches to the last bit.
3. **Corrupted extraction of the notebook code.** Pulling the table functions out of the `.nb` file's box format, the first attempt misjudged where `tableContributers` ended and copied 60 lines of unrelated text, plus a duplicate `reportFunction1`, into the `.wl` file. Listing every definition in the output and a bracket-balance check caught it.
4. **A test runner that could not import its own code.** The first runner imported the code under test before adding `src/` to the path. Running it once exposed the error.
5. **The VaR mixture parameters, a trap a reader could easily miss.** `DistFn1.m` sets α = 0.05 and β = 3, but the notebook's `varsumm` quietly uses α = 0.01 and β = 5. Trusting `DistFn1.m` would have reported a mixture VaR of \$2.22 million instead of \$1.68 million, overstating capital at risk by about a third. The AI flagged the switch while reading the notebook, and a hand calculation confirmed it: 0.99·Φ(−3.0325) + 0.01·Φ(−0.6065) = 1/255 at the displayed \$1,680,000.
6. **A tolerance too loose for fractional holdings.** In scenario 3, holdings of 12.5 were compared with a tolerance of one whole unit and so reported as "within one unit" rather than identical. Reading the summary line by line caught it; the tolerance now follows the number of decimals shown.
7. **Unverified claims labelled, not hidden.** Until Mathematica could run, scenario comparisons were reported as NO REFERENCE and two tests as SKIPPED rather than passing. The export scripts, written without a kernel, then ran unchanged. One export step failed twice on the £ and € symbols before it worked, and every transferred file was confirmed against a checksum: MD5 computed in Mathematica for the table values, SHA-256 computed in the browser for the notebook PDFs, which the browser pane could not download directly.

## How the AI's explanation was checked against the code

Every Part I claim was checked against the source line behind it rather than taken on trust: `n = 9` and `i < Length[seclist]` in the display cell, `Pick[marketDataValues, ...]` inside `eqtyFutpv`, `alpha = 0.01; beta = 5` inside `varsumm`, and `Sign[riskFactorBumpUnit]` in `populateVCV`. Hand calculations confirmed the headline numbers: CAC exposure of 7 + 0.7 × 5 = €10.5 million equivalent, or \$13.65 million at 1.30, which at a 0.025365 daily volatility gives the displayed \$346,200; and a normal VaR of \$616,900 × (−2.658) = −\$1.64 million.

The lesson is not that AI cannot translate this code. It translated nearly all of it correctly on the first pass. The open question is how much checking a team is willing to fund, because the errors that survive are the ones no one went looking for.
