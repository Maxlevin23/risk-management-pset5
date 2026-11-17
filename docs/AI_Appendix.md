---
title: "Problem 5: AI Appendix"
subtitle: "PPHA 42525 Risk Management, Autumn 2026 (not counted in the 2-page report)"
geometry: "margin=1.8cm"
fontsize: 10pt
mainfont: "Helvetica Neue"
monofont: "Menlo"
monofontoptions: "Scale=0.8"
---

## Tool

Claude Code (Anthropic), working directly in the project folder with the three Mathematica source files and the assignment PDF. It read the files, wrote the code, and ran it. Mathematica was run in Wolfram Cloud through a signed-in browser session, using the export script the AI wrote.

## Final prompts

The work was done in one agentic session, not as a separate prompt per part. The prompts below are quoted exactly as typed (spelling included). The assignment PDF was attached to the first one, and the AI took the per-part requirements (Parts I to IV, the pitfalls, the deliverables list) directly from that PDF.

**Prompt 1 (Parts I to IV in one request), with `problem5_Q.pdf` attached:**

> heres the latest assignment for risk management, i want you to complete everything outlined by the assignment, output the code in the risk mangement folder, the neatly organized python code, a pdf, doc of the code, the mathematica code with it, the explanations requested as their own document, and then check the code to make sure it matches the tables

**Prompt 2 (packaging and deliverables):**

> now format everything for assignment submission neatly in my risk mangement folder, as well as the pdf output of the code and the explanations that the professor wants submitted

**Prompt 3 (repository and remaining items):**

> push the checkpoint to its own title as risk mangement pset 5 and then finish all the open stuff please

Two shorter prompts in between asked the AI to commit and to push.

**Standing instructions the AI also read.** The Problem 2 system prompt (`Mathematica_to_pythonPrompttemplate.md`) was in the project folder and the AI read it before writing code. Its rules carried over: numpy, pandas and the standard library only; plain functions; descriptive names; no global variables inside functions; functions of about 40 lines; docstrings that state arguments, units and return values; preserve the Mathematica logic and flag ambiguity instead of guessing.

**How the Problem 2 prompt should be revised for this task.** It was not re-sent in revised form, but four changes describe what the AI did beyond it and belong in the prompt next time: (1) pass the `SamplePort2.m` data into every function as an argument, so a market-data scenario cannot leak into the base data; (2) name the Mathematica function each Python function translates in its docstring; (3) report functions return raw, unrounded numbers and a separate layer does all rounding and layout; (4) identify positions by their place in `seclist`, never by security name, and never report something as verified that was not actually compared.

## What the AI got wrong, and how it was caught

1. **Double rounding in the display layer.** The first `NumberForm` translation rounded to *n* significant figures and then to *f* decimals. For the CAC index volatility 0.025365051 that gives 0.025365 and then 0.02536; Mathematica shows 0.02537. Caught by comparing the first full run with the notebook PDF, cell by cell. Fixed by rounding once, to the coarser of the two precisions.
2. **Division where Mathematica multiplies by a reciprocal.** Two DV01s on FTE Equity are both 6,500,000 to within 1e-8 and display with one digit; Mathematica shows `7×10^6` for one and `6×10^6` for the other, Python showed `7×10^6` for both. The AI first reported this as unavoidable floating-point noise. The full-precision Mathematica export showed the exact values (6500000.000000022 and 6499999.999999975), and trying the possible operation orders showed that Mathematica computes `a*b*x/fx` as (a·b) × (x × fx⁻¹). With `eqtypv` and `eqtyFutpv` written that way the values agree to the last bit and the cell matches.
3. **Corrupted extraction of the notebook code.** Pulling the table functions out of the `.nb` file's box format, the first attempt mis-detected where `tableContributers` ended and copied 60 lines of unrelated text and a duplicate of `reportFunction1` into the `.wl` file. Caught by listing every definition in the output file and by a bracket-balance check.
4. **Test file that could not be imported.** The first test runner imported the code under test before adding `src/` to the path. Caught immediately by running it.
5. **Something a reader could easily miss: the VaR mixture parameters.** `DistFn1.m` sets alpha = 0.05 and beta = 3; the notebook's `varsumm` quietly uses alpha = 0.01 and beta = 5. The AI flagged this while reading the notebook; it was confirmed by hand (0.99·Φ(−3.0325) + 0.01·Φ(−0.6065) = 1/255 at the displayed 1,680,000).
6. **Display tolerance set too loosely for fractional holdings.** In scenario 3 the holdings of 12.5 were compared with a tolerance of one whole unit, so they were reported as "within one unit" instead of identical. Caught by reading the summary line by line after the first scenario comparison; the tolerance now follows the number of decimals shown.
7. **Unverified claims were labelled, not hidden.** Until Mathematica could be run, the scenario comparisons were reported as NO REFERENCE and two tests as SKIPPED instead of passing. The export scripts, written without a kernel, then ran unchanged; one export step failed twice on the encoding of the £ and € symbols before it worked, and the transferred file was confirmed against an MD5 checksum computed in Mathematica. The scenario notebook PDFs could not be downloaded through the browser pane (downloads, the clipboard and requests to the local machine were all blocked), so they were moved as compressed text and confirmed against SHA-256 fingerprints computed in the browser.

## How the AI's explanation was checked against the code

The Part I claims were checked against the source lines, not taken on trust: `n = 9` and `i < Length[seclist]` in the display cell; `Pick[marketDataValues, ...]` inside `eqtyFutpv`; `alpha = 0.01; beta = 5` inside `varsumm`; `Sign[riskFactorBumpUnit]` in `populateVCV`. Hand calculations confirmed the numbers: CAC exposure (7 + 0.7 × 5) × 1.3 = EUR 10.5mn equivalent, 13.65mn × 0.025365 = 346,200; normal VaR 616,900 × (−2.658) = −1,640,000.
