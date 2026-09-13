# Cursor silver adjudication findings

Panel: five isolated judges plus resolver, all `cursor-grok-4.6-high-fast`.
This is **one model family**. It is **not** independent human validation.
GLM-5.3 contributes only the separate frozen Stage A replication panel.
Partial GLM Stage B is provenance only and is excluded from A→B→C math.

## Cohort

- 1,061 unique claims (226 regressions, 335 resistant, 250 rescue, 250 robust).
- Judged N = 1,060 after excluding provider-filtered `SA-000352`.
- Blinded progressive disclosure: Stage A (sentences) → Stage B (titles) →
  Stage C (reconstructed structured evidence only; no new retrieval).

## Within-Cursor-panel agreement

Label: **within-Cursor-panel agreement**.

| Stage | Pairwise agreement | Fleiss κ | Krippendorff α | Consensus |
| --- | ---: | ---: | ---: | --- |
| A | 89.8% | 0.846 | 0.846 | Refuted 403 / Supported 349 / Ambiguous 277 / Unresolved 31 |
| B | 95.3% | 0.928 | 0.928 | Refuted 423 / Supported 375 / Ambiguous 241 / Unresolved 21 |
| C | 95.4% | 0.928 | 0.928 | Refuted 437 / Supported 392 / Ambiguous 212 / Unresolved 19 |

Decisive-only pairwise agreement is essentially 1.0. Residual disagreement is
mostly Ambiguous vs decisive, not Supported vs Refuted.

Resolver (non-high-consensus items only; anonymized `r1`–`r5`; same locked
model): Stage A 308, Stage B 262, Stage C 231 items.

## Cross-panel Stage A replication (GLM vs Cursor)

This is **replication, not human validation**. Cursor judges never saw GLM
outputs.

- Modal verdict agreement 0.862; consensus agreement 0.831; ambiguity
  agreement 0.855.
- Cursor Stage A is more ambiguous (29.1%) than GLM (22.3%).
- Regression ambiguity is similar (Cursor 45.6% vs GLM 41.6%).

## Twelve confirmatory questions

Rates use Ambiguous+Unresolved as the ambiguity event. CIs are percentile
bootstrap (2,000; seed 20260822). Odds ratios compare the named cohorts.

**Q1.** Stage A ambiguity is much higher in regressions (45.6%) than robust
controls (9.6%); OR 7.89, BH-adjusted p ≪ 0.001. Resistant (42.8%) resembles
regression, not robust.

**Q2.** Titles resolve 7.1% of regressions vs 6.0% of robust (OR 1.19, n.s.).
Title disclosure is not a regression-specific fix.

**Q3.** Structure-only resolution is higher in regressions (5.3%) than robust
(0.4%); OR 13.96, BH p = 0.0016. The effect is real but small in absolute
rate.

**Q4.** Resistant vs robust Stage A and Stage C ambiguity ORs are large
(7.05 and 13.51). Resistant vs regression ORs are near 1 (0.89 and 0.82).
Resistant failures resemble regressions.

**Q5.** Shared vs model-specific regressions do not differ on title or
structure resolution. Shared regressions are more likely to remain ambiguous
after Stage C (OR 3.00, BH p = 0.0031).

**Q6.** Ambiguity declines A → B → C: 29.1% → 24.7% → 21.8% overall, and
45.6% → 42.0% → 38.1% in regressions. Paired McNemar tests are significant
for A→B, B→C, and A→C.

**Q7.** Consensus changes A→B on 9.7% of items (12.4% of regressions).

**Q8.** Consensus changes B→C on 6.1% of items (8.4% of regressions).
Consensus-level reversals of a decisive verdict are 0 at both steps.

**Q9.** After Stage C, 61.9% of regressions are high-consensus Supported or
Refuted, versus 96.4% of robust controls.

**Q10.** Representation-sensitive taxonomy covers 11.9% of regressions
(11.1% resistant, 6.4% robust).

**Q11.** Residual Stage C ambiguity is 38.1% of regressions and 21.8% of all
judged items.

**Q12.** Cursor Stage A/C ambiguity is associated with both local NLI
diagnostics (φ 0.13–0.19). The association is detectable and modest: NLI
disagreement does not substitute for the silver label.

## Mechanism decision

**Mixed.** Do not force a single mechanism.

- **Warrant ambiguity** is the largest residual: 38.1% of regressions remain
  Ambiguous/Unresolved after full structured evidence, and 21.8% of the
  whole panel do. Shared regressions concentrate this remainder.
- **Evidence-utilization failure** is also large: 50.0% of regressions
  receive a decisive high-consensus Stage C verdict (taxonomy
  `silver_clear_evidence_utilization_failure`), so many GPT regressions
  occur on claims the Cursor panel treats as clearly warranted.
- **Representation-sensitive** is the smaller share (11.9% of regressions).
  Titles do not preferentially resolve regressions; structure helps a little
  and does not reverse decisive consensus labels.

Cursor-vs-GLM Stage A already showed Cursor is the more ambiguity-conservative
family. Residual Stage C ambiguity could still be warrant-intrinsic, or the
same-family conservatism repeating under full disclosure.

## One next experiment (not run)

> **Historical note.** This section records the experiment as proposed at the time this report was frozen. The 231-item Claude residual Stage C panel was subsequently run (`../claude_residual_panel/`). A later Claude A→B→C panel on all 226 regressions is the main cross-family replication (`../claude_full_regression_panel/`). Do not read the heading as current project status. The original text below is unchanged.

Run a **locked different-model-family Stage C panel on the 231 residual
Ambiguous/Unresolved items only**, same blinded reconstructed evidence,
same rubric, no GLM or Cursor outputs shown. That is the cheapest test of
whether residual ambiguity is warrant-intrinsic versus Cursor-family
conservatism. Do not rerun GPT. Do not expand to a new cohort first.
