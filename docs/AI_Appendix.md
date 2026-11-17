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

Claude Code (Anthropic), working directly in the project folder with the three Mathematica source files and the assignment PDF. It read the files, wrote the code, and ran it; it could not run Mathematica.

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
2. **A value on a rounding boundary.** Two DV01s are exactly 6,500,000 and display with one digit. The first version showed both as `6×10^6`; after fix 1 both show `7×10^6`; Mathematica shows one of each. Investigation showed the digit is decided by floating-point noise near 1e-8, so this is reported as a known one-unit discrepancy instead of being forced.
3. **Corrupted extraction of the notebook code.** Pulling the table functions out of the `.nb` file's box format, the first attempt mis-detected where `tableContributers` ended and copied 60 lines of unrelated text and a duplicate of `reportFunction1` into the `.wl` file. Caught by listing every definition in the output file and by a bracket-balance check.
4. **Test file that could not be imported.** The first test runner imported the code under test before adding `src/` to the path. Caught immediately by running it.
5. **Something a reader could easily miss: the VaR mixture parameters.** `DistFn1.m` sets alpha = 0.05 and beta = 3; the notebook's `varsumm` quietly uses alpha = 0.01 and beta = 5. The AI flagged this while reading the notebook; it was confirmed by hand (0.99·Φ(−3.0325) + 0.01·Φ(−0.6065) = 1/255 at the displayed 1,680,000).
6. **A limit, not an error.** The AI had no Mathematica kernel, so it could not produce the scenario references or full-precision function values. It wrote the export script and marked those comparisons NO REFERENCE and SKIPPED instead of reporting them as passing. The Mathematica scripts themselves are untested until they are run.

## How the AI's explanation was checked against the code

The Part I claims were checked against the source lines, not taken on trust: `n = 9` and `i < Length[seclist]` in the display cell; `Pick[marketDataValues, ...]` inside `eqtyFutpv`; `alpha = 0.01; beta = 5` inside `varsumm`; `Sign[riskFactorBumpUnit]` in `populateVCV`. Hand calculations confirmed the numbers: CAC exposure (7 + 0.7 × 5) × 1.3 = EUR 10.5mn equivalent, 13.65mn × 0.025365 = 346,200; normal VaR 616,900 × (−2.658) = −1,640,000.
