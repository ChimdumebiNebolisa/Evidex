# Targeted Evidex revision report

Authoritative baseline: October 11 TeX SHA256 `24621723250b4b40099880f7aef7bb7d23a2dbd8721df54ab8f776988d537b7c`. Revised master: `d09c13421c40ba5e48d286b88c6c8af83c211e74e43dc8063d5e14a2f99e31eb`. The baseline PDF and source remain byte-identical at their original paths and under `baseline/`.

## Changes made: exact files and locations

Scientific text changes are confined to `manuscript.tex`: 14 existing paragraphs revised, with N1 split into N1/N2. Title, organization, Section 2 subsections, tables, figures, equations, citation commands, bibliography and reported numerical values are unchanged. Supporting ledgers and reports were refreshed; no research data or execution files were edited.

| Paragraph | Section | Revised source line |
|---|---|---|
| ABS1 | Abstract | 19 |
| I3 | Introduction | 30 |
| I5 | Introduction | 36 |
| RW4 | Evidence-related prediction changes | 51 |
| RW6 | Evidence judgments and evaluator sensitivity | 58 |
| RQ1 | Research questions | 84 |
| X4 | Analysis and correction choices | 112 |
| N1 | Supporting natural language inference diagnostic | 148 |
| D1 | Interpretation of the linked findings | 224 |
| CON1 | Conclusion | 248 |
| B2 | Accuracy gains and regressions | 122 |
| D3 | Evaluation implications | 231 |
| L3 | Limitations | 244 |
| APB2 | Correction and execution provenance | 268 |
| N2 | Supporting natural language inference diagnostic | 151 |

## Before/after and scientific justification

| Item | October 11 baseline | Targeted revision | Why it improves the argument |
|---|---|---|---|
| RQ2 | Frequency and overlap only; Section 4.4 claimed the question was answered | Frequency, overlap and observable claim–evidence characteristics; Section 4.4 gives a partial answer and Section 4.5 supplies exploratory characterization | The stated question now matches the analyses already reported, without adding an experiment or result |
| Contribution and gap | The paired findings and family comparison were linked, but the NLI component was largely absent from the contribution and gap | Paired behavior → exploratory evidence characterization → matched judge-family measurement, with explicit boundaries from established evidence-sensitivity literature | Makes the distinctive combined analysis visible without claiming that evidence benefits, context sensitivity or robustness concerns are new discoveries |
| Section 4.5 | One paragraph moved directly into NLI disagreement rates | Two paragraphs explain why all transition categories are compared, retain the rates and two model identifiers, then bound the shared failure-category association and predictive limits | Prevents interpreting a common error-category characteristic as a unique regression signature, benchmark error or cause |
| Correction timing | General post hoc wording could blur protocol timing and A1 timing | September 27 correction freeze precedes fresh corrected C judgments; A1 follows execution/provisional inspection and changes specific rules | Preserves both the prospective timing of the new judging specification and the actual post-execution amendment uncertainty |

The exact requested RQ2 is: **How frequently do correct-to-incorrect transitions occur, how much do they overlap across predictors, and what observable claim–evidence characteristics accompany these regressions?** RQ1, RQ3 and RQ4 remain unchanged.

The targeted literature check used the existing primary papers. Vitamin C studies contrastive evidence, Longpre studies constructed knowledge conflicts in question answering, FactEval perturbs claims while preserving evidence, and Chen studies judge bias in generated-response evaluation. Those distinctions remain explicit. The gap is the linked measurement within this fixed study, not an assertion that no prior work has examined any individual component. No citation was added or removed.

`NOVELTY_BOUNDARIES.md` supplied provisional joint-contribution ideas, not evidence of absolute novelty. Stronger source wording about mechanisms or unique regression signals was not imported. Archived NLI results, actual artifact counts and later A1 selections control scientific interpretation. The earlier post-judgment note’s proposed first-valid main estimate does not supersede A1’s accepted-output main analysis.

## Verification actually completed

- Studio doctor found the isolated analysis dependencies and configured Tectonic 0.17.0. New output initialized in revise mode; same-hash writing/review/ai-review instructions read earlier in this conversation were reused.
- First Tectonic build passed. No overfull/underfull boxes, unresolved citations/references or missing glyph diagnostics. All 17 actual PDF page images and five unchanged standalone figures were viewed.
- 49 targeted checks passed: exact title/date/section/citation/label/caption/table/display preservation, unchanged scientific numerical tokens, exact unchanged RQ1/RQ3/RQ4, requested RQ2, dependent answer scope, limits and timing. Sixteen of these checks independently grouped existing records to reproduce both NLI models across all transition categories; four confirm the retained main-text values.
- 51 existing manuscript scenarios passed: raw predictor accuracy/gains, regression union/overlap, family totals, accepted/first-valid results, denominator distinctions, Section 3 scope, withdrawals, qualifications and original-source preservation. No model inference, refit or experiment rerun occurred.
- Studio numerical integrity passed for all 54 source-bound paragraphs and five unchanged displays. All nine citation identities passed after documented reconciliation of AmbiFC’s XML title formatting; the raw automatic mismatch is preserved. All 11 source occurrences have refreshed support records. Changed literature contexts were reread against primary sources.
- The writing scan retains FINDINGS for LaTeX/hyperlink repetitions and established taxonomy-label hyphenation. Located manual dispositions are in `reports/writing-findings-reviewed.json`; it was not relabeled as an automated clean prose pass.

## Concrete unresolved concerns

No evidence-dependent editorial correction remains open. Existing scientific limits remain explicit: the predictor contrast combines instruction and evidence changes; NLI and feature associations do not identify causes or validate FEVER errors; raw valid predictor completions are absent; duplicate-text dependence is not adjusted in the archived record-level intervals; judge outputs are silver judgments without human validation; historical A/B context transcripts and immutable provider snapshots are unavailable; the taxonomy remains proposed and requires coauthor review; A1 is post-execution and the original frozen-protocol primary remains incomplete. None is silently resolved through prose or presented as a new prerequisite for these editorial changes.

Optional improvements: none added to the required scope. Venue-specific compliance remains unassessed because no venue was selected.

## Artifacts and result

- `manuscript.pdf`: revised, compiled and visually inspected 17-page paper.
- `manuscript.tex`, `references.bib`, `figures/`, `tables/`: editable scientific master and unchanged compilation inputs.
- `october11-targeted.diff`: exact unified diff; `october11-targeted-diff.html`: readable side-by-side source comparison.
- `targeted-changes.json`: exact before/after paragraph text and revised locations.
- `targeted-requirements.json`, `research-model.json`, `claims.json`, `citation-support.json`: refreshed scope/evidence records.
- `reports/targeted-verification.json`, `reports/manuscript-scenarios.json`, `reports/final-status.json`: actual check scopes and final status.

Result: a stronger presentation of the same recorded research, ready for neutral coauthor review within the stated scientific limits. No title change, figure change, data/protocol modification, commit, push, PR, submission or publication was performed.
