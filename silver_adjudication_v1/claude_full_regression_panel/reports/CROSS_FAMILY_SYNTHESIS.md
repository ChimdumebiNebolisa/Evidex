# Cross-family synthesis — Claude vs Cursor/Grok on all 226 regressions

> **Does a fully independent Claude A→B→C panel on all 226 regressions
> reproduce the mixed-mechanism picture originally derived from the
> Cursor/Grok panel?**
>
> **Yes for the qualitative picture, no for the proportions.** Both families
> independently find all three mechanisms present, with evidence-utilization
> failure the largest and representation-sensitivity the smallest. But Claude
> shifts substantial mass from residual ambiguity and representation-sensitivity
> into evidence-utilization failure, and the two panels disagree on roughly one
> regression in four.

Both panels are model-based silver adjudication. Agreement between them does
not establish human ground truth, and disagreement with FEVER does not
establish FEVER annotation error.

## Overall mechanism proportions

| Mechanism | Grok n | Grok % | Claude n | Claude % | Δ (pp) |
|---|---|---|---|---|---|
| Evidence-utilization failure | 113 | 50.0% | 149 | 65.9% | +15.9 |
| Representation-sensitive | 27 | 11.9% | 12 | 5.3% | −6.6 |
| Residual ambiguity | 86 | 38.1% | 65 | 28.8% | −9.3 |
| Other / unresolved | 0 | 0.0% | 0 | 0.0% | 0.0 |

The rank order of the three mechanisms is identical across families. The
magnitudes are not: Claude's utilization-failure share is 15.9 points higher,
and its 95% CI (59.5–71.8) does not overlap Grok's (43.5–56.5).

## Claim-level agreement

- Exact taxonomy agreement: **74.3%** (168/226)
- Broad-category agreement: **74.3%** (identical, because neither panel assigns
  any item to `silver_title_context_sensitive`)
- Cohen's kappa on the broad categories: **0.537** — moderate

Confusion matrix, rows = Grok, columns = Claude:

| | Claude: utilization | Claude: representation | Claude: residual |
|---|---|---|---|
| **Grok: utilization** | 107 | 1 | 5 |
| **Grok: representation** | 20 | 4 | 3 |
| **Grok: residual** | 22 | 7 | 57 |

The disagreement is directional, not noise. Claude reclassifies 20 of Grok's 27
representation-sensitive cases and 22 of Grok's 86 residual-ambiguity cases as
utilization failures, while moving only 6 cases the other way. Grok's
representation-sensitive category is the least stable: Claude retains only 4 of
27.

## Stage-level comparison

| Measure | Grok | Claude | Δ (pp) | McNemar p |
|---|---|---|---|---|
| Stage A ambiguity | 45.6% | 29.2% | −16.4 | 7.8e-10 |
| Stage B ambiguity | 42.0% | 28.3% | −13.7 | 3.4e-07 |
| Stage C ambiguity | 38.1% | 28.8% | −9.3 | 7.5e-04 |
| Resolved by titles | 7.1% | 4.0% | −3.1 | 0.143 |
| Resolved by structure | 5.3% | 3.1% | −2.2 | 0.359 |
| Final non-decisive after C | 38.1% | 28.8% | −9.3 | 7.5e-04 |
| Reversal after titles | 0.0% | 0.0% | 0.0 | 1.000 |
| Reversal after structure | 0.0% | 0.0% | 0.0 | 1.000 |

This is the mechanism behind the taxonomy difference. Claude is systematically
more willing to reach a decisive verdict on the same evidence — its ambiguity
rate is significantly lower at every stage — so items Grok leaves ambiguous
become utilization failures under Claude. The gap narrows as disclosure
increases (16.4 → 13.7 → 9.3 points), meaning the two families converge
somewhat once structured evidence is available.

Both families agree on the two qualitative facts about progressive disclosure:
title and structure disclosure resolve only a small share of ambiguity (the
differences between panels here are not significant), and **neither family ever
reverses a decisive consensus** after additional disclosure.

## Shared vs model-specific regressions

| Subgroup | n | Grok residual ambiguity | Claude residual ambiguity |
|---|---|---|---|
| Shared by both GPT models | 40 | 60.0% | 47.5% |
| One GPT model only | 186 | 33.3% | 24.7% |

Both families independently find that regressions shared by both GPT models are
far more likely to remain non-decisive than model-specific ones. The absolute
levels differ in the same direction as everywhere else (Claude lower), but the
contrast replicates.

## Conclusions by robustness class

**Robust across both judge families**

- All three mechanisms are present; none is negligible and none dominates
  completely. The mixed-mechanism interpretation survives.
- Evidence-utilization failure is the single largest mechanism.
- Representation-sensitivity is the smallest mechanism, in single digits to low
  double digits.
- Additional disclosure (titles, then structured evidence) resolves only a
  small minority of ambiguous cases.
- No decisive consensus is ever reversed by additional disclosure, in either
  family.
- Shared regressions are more persistently ambiguous than model-specific ones.

**Quantitatively different but directionally consistent**

- The exact split between utilization failure and residual ambiguity. Both
  families rank utilization failure first, but Claude puts it at 65.9% against
  Grok's 50.0%, with non-overlapping confidence intervals.
- Stage-wise ambiguity levels: same ordering and same shrinking trend, offset
  by roughly 9–16 points.

**Judge-family-sensitive**

- The absolute ambiguity rate at every stage. This is the primary axis of
  disagreement and it drives everything downstream.
- The representation-sensitive category specifically. Grok's 27 cases and
  Claude's 12 overlap on only 4 items, so which individual claims count as
  representation-sensitive is not stable across families, even though the
  category stays small in both.
- Per-claim mechanism assignment generally: kappa 0.537 means a quarter of
  claims would be labelled differently depending on the judge family.

**Unresolved without human adjudication**

- Whether Claude's lower ambiguity rate reflects better evidence utilization or
  overconfidence on genuinely under-warranted claims. Nothing in this design can
  distinguish those, since both panels are models scoring the same evidence.
- Consequently, the true mechanism proportions. The cross-family range for
  utilization failure is 50–66%; picking a point estimate inside it would
  require an arbiter neither panel provides.
- Whether the 58 claim-level disagreements concentrate on a recognisable class
  of claims. That requires human adjudication of those specific items.

## What this does and does not license

It licenses the qualitative claim that GPT regressions under FEVER evidence
arise from a mixture of mechanisms rather than a single cause, and that
evidence-utilization failure is the leading one. It does not license quoting a
precise decomposition as if it were judge-independent: the headline split moves
by roughly 16 points when the judge family changes.
