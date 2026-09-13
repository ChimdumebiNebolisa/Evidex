# Final Evidex strengthening synthesis

> **Intermediate synthesis.** This document was the layer-by-layer write-up after the Claude residual Stage C panel. A subsequent Claude five-judge A→B→C panel on all 226 unique regressions is now the main cross-family replication. The canonical final synthesis is [`../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`](../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md). Numbers in this file are unchanged and remain valid for the residual experiment.

> **Scope of later body language.** Phrases such as “last planned experiment” describe the study state when this residual write-up was frozen. “Claude does not re-open” the Grok 50.0/11.9 shares referred only to this residual-conditioned design (Claude judged the 231 leftovers, not the already-decisive Grok regressions). Those sentences are not study-level conclusions after the later full Claude A→B→C replication. The historical body below is unchanged.

Evidex now has six automated layers. They answer different questions.
Do not collapse them into one validation percentage.

## 1. Original GPT fact-checking experiment

GPT-5.4 and GPT-5.4-mini claim-only vs evidence transitions on FEVER.
Establishes the behavioral phenomenon (regressions, resistant errors,
rescues) that later layers try to locate. Does not locate the warrant.

## 2. Analysis v2 transition decomposition

Paired features, NLI diagnostics, and cohort construction (226
regressions, 335 resistant, 250 rescue, 250 robust; 1,061 unique claims).
Establishes measurable correlates. Does not adjudicate evidence
sufficiency.

## 3. Two local NLI diagnostics

Detectable, modest association with later silver ambiguity. NLI
disagreement is not a substitute for a silver label.

## 4. Frozen GLM Stage A replication

Separate GLM-5.3 Stage A panel vs Cursor Stage A. Replication, not
human validation. Modal verdict agreement 0.862. Cursor is the more
ambiguity-conservative family at sentence-only evidence. Partial GLM
Stage B is provenance only and is excluded from A→B→C math.

## 5. Grok A→B→C progressive-disclosure panel

Five isolated `cursor-grok-4.6-high-fast` judges, judged N = 1,060.
Ambiguity falls 29.1% → 24.7% → 21.8% overall; regressions remain high
at Stage C (38.1%). Mechanism on the full panel was already **mixed**:
warrant ambiguity is the largest residual, evidence-utilization failure
is also large, representation-sensitive is smaller. Same-family
limitation: residual Stage C ambiguity could still be Grok conservatism.

## 6. Claude Stage C residual validation (this study)

Five isolated `claude-opus-5-thinking-high` judges on the 231 Grok
Stage C leftovers only. Raw consensus: **58.0%** remain
Ambiguous/Unresolved; **42.0%** become high-consensus decisive; Claude
internal disagreement 0. Shared regressions stay the stickiest residual
slice. This is the cross-family test that the Cursor panel named as the
single next experiment.

## Final mechanism assessment

**Mixed.**

Quantitatively, on the Grok Stage C residual:

- Cross-family persistent ambiguity 134/231 = 58.0% (CI 51.5–64.1).
- Grok-only high-consensus resolution 97/231 = 42.0% (CI 35.9–48.5).
- Residual regressions persist more than residual resistant items
  (68.6% vs 53.6%; OR 1.89).
- On the full Cursor panel, 50.0% of regressions were already
  high-consensus decisive after Stage C (utilization failure) and 11.9%
  were representation-sensitive. Those full-panel shares are unchanged;
  Claude does not re-open them.

So Evidex should not say “the failures are mostly missing titles,” nor
“the residual is only Grok being cautious,” nor “the residual is proven
intrinsically ambiguous.” The supported statement is mixed: a substantial
cross-family leftover remains under full structured evidence, and a
substantial leftover is family-dependent.

## What is finished

This was the last planned strengthening experiment. No further model
family, GPT rerun, cohort expansion, silver panel, or feature-mining
pass is required to complete Evidex strengthening. Remaining work is
synthesis, paper framing, or separate research.

Claude judgments are not human ground truth. Automated-family limits
remain. There is no causal claim about GPT internals.
