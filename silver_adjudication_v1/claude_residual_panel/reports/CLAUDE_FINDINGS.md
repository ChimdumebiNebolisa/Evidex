# Claude residual Stage C findings

Panel: **five isolated judges**, all `claude-opus-5-thinking-high`.
This is a **cross-family residual Stage C robustness test**, not
independent human validation. Judges never saw Cursor/Grok, GLM, FEVER, GPT,
NLI, cohort, or prior Claude outputs.

Primary result: **raw five-judge consensus**. No resolver was run.

## Cohort

- Independently reconstructed **231 residual** Cursor Stage C items
  (**212 Ambiguous** + **19 Unresolved**).
- Opaque IDs `CR-000001`–`CR-000231`; Stage C evidence only.
- Residual mix after later unblinding: **112 resistant**, **86 regression**,
  **24 rescue**, **9 robust**.

## Completeness

- Raw judgments: **1,155** (231 × 5). Each judge 231/231.
- Batches 01–02 completed on the first Cursor account (770 judgments).
- Batch 03 (77 items × 5) resumed on a second Cursor account after the
  first account exhausted its Claude usage allowance. Model slug, rubric,
  packets, and protocol were unchanged. Schema retries: 0.

## Raw Claude consensus

Ambiguous 130 / Supported 63 / Refuted 34 / Unresolved 4.

- Persistent Ambiguous/Unresolved: **134/231** = **58.0%**
  (bootstrap 95% CI **51.5–64.1**).
- Decisive: **97/231** = **42.0%**. Every decisive item is high consensus
  (`>=4/5`); **high-consensus rate 42.0%**.
- claude_internal_disagreement 0.

## Within-Claude-panel agreement

Label: **within-Claude-panel agreement**.

| Pairwise | Fleiss κ | Krippendorff α | High-consensus | Ambiguous+Unresolved |
| ---: | ---: | ---: | ---: | ---: |
| **87.9%** | **0.802** | 0.802 | 42.0% | 58.0% |

Judge-level Ambiguous rates sit in a narrow band (49.4–51.5%).
Panel **mean confidence 63.2**. Mean within-item confidence SD is 2.2.

## Cross-family result (after freeze)

Cursor Stage C on this set is residual by construction. Exact consensus
label agreement is **56.3%** (**join n=231**): Claude Ambiguous matches
Cursor Ambiguous on 128 items; the remaining persistent cases are
Ambiguous/Unresolved mismatches (6) plus the 97 Claude-decisive items.

Cross-family taxonomy:

- `cross_family_persistent_ambiguity` **134/231** (58.0%)
- `grok_only_ambiguity` **97/231** (42.0%; all high-consensus) — Claude-resolved Grok residuals
- `claude_internal_disagreement` 0

After FEVER unblinding of Claude-decisive items: **62/97** ( **63.9%** )
agree with FEVER gold; **35/97** disagree. Do not treat FEVER disagreement
as benchmark error.

## Subgroups (exploratory)

Persistent Ambiguous/Unresolved rates:

| Residual subgroup | n | Persistent |
| --- | ---: | ---: |
| 24 shared regressions | 24 | **75.0%** |
| 62 model-specific regressions | 62 | **66.1%** |
| 86 regression residuals | 86 | **68.6%** |
| 112 resistant residuals | 112 | **53.6%** |
| 24 rescue residuals | 24 | 50.0% |
| 9 robust residuals | 9 | 33.3% |

Regression vs resistant persistence **OR 1.89** (95% CI 1.05–3.41;
Fisher p = 0.040, BH-adjusted p = 0.040). Shared-regression n=24 and
robust n=9 are small.

Mean Claude confidence is lower on persistent items (**59.9**) than on
resolved items (**67.9**; Mann–Whitney p ≪ 0.001).

Dominant issue flag on persistent items is `partial_warrant` (103/134),
then `entity_or_attribute_confusion` (52) and missing surrounding context
or numerical/temporal reasoning (41 each). Flags are judge-assigned
diagnostics, not gold labels.

## Mechanism

**Mixed.** A majority of Grok Stage C residuals remain Ambiguous/Unresolved
under Claude (58.0%, CI 51.5–64.1), which supports a cross-family warrant
difficulty reading. A substantial minority become high-consensus decisive
(42.0%, CI 35.9–48.5), which is Grok-family-specific residual conservatism
on this set. Do not collapse those two shares into one mechanism.
