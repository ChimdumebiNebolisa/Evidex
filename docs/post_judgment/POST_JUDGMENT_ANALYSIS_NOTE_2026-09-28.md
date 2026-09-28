# Post-judgment deviation analysis — dated amendment, 2026-09-28

Label: `PROVISIONAL_DEVIATION_ANALYSIS__NOT_FROZEN_PROTOCOL_PRIMARY`

This note was written **after** all 70 required Stage C outputs and every failed attempt had been
inspected. It is not preregistered and not part of the frozen correction protocol
(`corrections_v2/protocol/analysis_spec_2026-09-27.md`, frozen 2026-09-27T06:35Z). That protocol and
its freeze are unchanged. As the protocol requires for any later change, this is a separately named,
dated analysis. The input selections below were chosen after the outputs and execution records were
seen. The categories are descriptive judge-panel outcomes. They do not establish FEVER label
errors or causes of GPT errors. Operational detail is in `TECHNICAL_SUPPLEMENT_2026-09-28.md`.

## 1. Frozen-protocol primary analysis: incomplete

`python corrections_v2/analysis_pipeline.py status --panel primary` reports `incomplete`, and this
stays the protocol's result. All 70 required jobs (55 Grok, 15 Claude; 6,430 judgments) delivered
schema-valid outputs. The frozen validator nevertheless rejects execution provenance for two reasons:

- six jobs used more than the frozen three attempts after quota and usage-limit failures;
- 13 collision records from concurrent runners carry session `unknown`, which the validator counts
  as reused sessions.

Consequences: no judgment freeze, no `corrections_v2/results/`, and no follow-up packets. The
protocol-defined downstream analyses have therefore **not** been run: the newly selected corrected
residual Claude panel and the Stage C resolver. The optional fixed historical residual panel (15 jobs /
1,155 judgments) was also not run.

## 2. Input selections

| Selection | Definition | Role |
|---|---|---|
| Accepted as delivered | the 70 accepted outputs | reference |
| First finished schema-valid (Claude) | `p02_C_j2_b02` slot 1 replaces slot 3; `p02_C_j2_b03` slot 1 replaces slot 4 | closest to the protocol's first-valid rule; proposed main deviation estimate (coauthor decision) |
| Grok `p01_C_j5_b09` slot 1 | the 100-row schema-valid file left by a run that ended with `[resource_exhausted]`, replacing accepted slot 2 | explicit sensitivity only; not part of the main estimate |
| 12 Claude combinations | every finished run for `p02_C_j2_b02` (slots 1–3) × `p02_C_j2_b03` (slots 1–4) | range over all completed-run choices |

In the two Claude jobs, earlier runs finished with valid outputs but were never checkpointed,
because a duplicate runner had already written collision records into their slots. A later run was
accepted instead, so the accepted outputs break the first-valid rule. The Grok slot-1 run wrote a
complete file and then ended in a provider error. Whether a run that did not finish counts as a
"response" under the first-valid rule is a judgment call, so that file is kept out of the main
estimate. In three other Claude jobs (`p02_C_j3_b01`–`b03`) and in both flagged Grok jobs, the
accepted output was the first output of any kind, so the first-valid rule holds there even though
those jobs exceed the attempt cap.

## 3. Results on the 226 unique regressions (same claims in both panels)

The categories come from the frozen descriptive v2 taxonomy. Consensus uses historical Stage A/B
judgments, which were retained under the documented protocol, plus the new Stage C judgments on the
repaired packets. This hybrid provenance is disclosed. Intervals are Wilson 95%.

| Category | Grok | Claude, accepted | Claude, first-valid |
|---|---:|---:|---:|
| Sentence-only gold-agreeing | 77 (34.1%, 28.2–40.5) | 106 (46.9%, 40.5–53.4) | 105 (46.5%) |
| Title-disclosure gold-agreeing | 10 (4.4%) | 3 (1.3%) | 3 (1.3%) |
| Structured-disclosure gold-agreeing, no added text | 2 (0.9%) | 3 (1.3%) | 6 (2.7%) |
| Additional-evidence gold-agreeing | 17 (7.5%) | 14 (6.2%) | 14 (6.2%) |
| Nonmonotonic judge path | 5 (2.2%) | 5 (2.2%) | 5 (2.2%) |
| Decisive judge–FEVER disagreement | 44 (19.5%, 14.8–25.1) | 54 (23.9%, 18.8–29.9) | 54 (23.9%) |
| Final nondecisive | 71 (31.4%, 25.7–37.7) | 41 (18.1%, 13.7–23.7) | 39 (17.3%, 12.9–22.7) |

| Measure | Accepted | First-valid |
|---|---|---|
| Nondecisive at A / B / C, Grok | 103 / 95 / 71 | same |
| Nondecisive at A / B / C, Claude | 66 / 64 / 41 | 66 / 64 / 39 |
| Resolved by titles (Grok / Claude) | 16 / 9 | same |
| Decisive consensus reversed after titles or at C | 0 in both panels | same |
| Exact cross-family taxonomy agreement | 172/226 = 76.1% (70.1–81.2), κ = 0.673 | 168/226 = 74.3% (68.3–79.6), κ = 0.651 |
| Claude − Grok nondecisive at C (exact McNemar, BH) | −13.3 pp, p_BH = 7.2×10⁻⁸ | −14.2 pp, p_BH = 9.1×10⁻⁸ |
| Claude − Grok sentence-only gold-agreeing | +12.8 pp, p_BH = 4.6×10⁻⁷ | +12.4 pp, p_BH = 2.1×10⁻⁶ |
| Claude − Grok decisive judge–FEVER disagreement | +4.4 pp, p_BH = 0.015 | same |
| Shared vs model-specific nondecisive odds ratio, Grok | 2.05 (1.02–4.13), p = 0.059 | same |
| Shared vs model-specific nondecisive odds ratio, Claude | 3.17 (1.47–6.83), p_BH = 0.011 | 3.47, p_BH = 0.0046 |

Across the two selections, every one of the 16 cross-family tests keeps its Benjamini–Hochberg
decision. The only sign change is in the non-significant `resolved_at_C` test, from −1.3 pp to 0.0.
The first-valid Claude selection changes the Stage C consensus of six claims (SA-000189, SA-000313,
SA-000458, SA-000583, SA-000867, SA-000966).

The new 74.3% agreement under first-valid happens to equal the historical 74.3% (168/226). The two
figures are not comparable. The historical one used the withdrawn legacy taxonomy on defective
Stage C packets.

**12 Claude combinations.** Between 0 and 6 claims change Stage C consensus relative to the accepted
selection, and Claude Stage C Ambiguous ranges from 37 to 42 of 226 (accepted: 41; first-valid: 39).

**Grok `p01_C_j5_b09` slot 1 (sensitivity decision).** Substituting the error-ending run's file
changes one Stage C consensus label, on SA-000834: a rescue-cohort claim that goes from Ambiguous to
Unresolved and stays final nondecisive. It also changes Stage C mean-confidence values for that
job's items. It changes no field of any regression-cohort claim, and no cross-family result.
`provisional_analysis.py verify` checks this directly. Across the 1,060-claim Grok panel,
nondecisive Stage C stays at 220 (Ambiguous 193→192, Unresolved 27→28). The committed
`sensitivity_first_valid_2026-09-28` result set contains this substitution. Verify mode shows that
its regression-cohort and cross-family numbers equal those from Claude first-valid alone.

## 4. What these results can support

- The legacy three-way ordering claim does not carry over. The v2 taxonomy defines no mapping onto
  the legacy categories. The legacy "utilization" bucket also contained decisive verdicts that
  disagree with FEVER, which v2 separates out (Grok 44, Claude 54). The nearest comparison,
  sentence-only gold agreement against final nondecisive, is 77 against 71 for Grok, with
  overlapping intervals, and 106 against 41 for Claude. "Utilization failure is largest in both
  panels" is therefore not a result of this analysis.
- A fifth to a quarter of regressions end with a decisive panel verdict that disagrees with FEVER
  (Grok 19.5%, Claude 23.9%). These are judge–FEVER disagreements, not evidence that FEVER is wrong.
- Sentence-only gold agreement is compatible with an evidence-utilization explanation of the GPT
  regression but does not establish it. The original GPT runs stored labels only.
- Titles make 16 of Grok's 103 Stage A-nondecisive regressions decisive. Stage C makes 27 of its 95
  Stage B-nondecisive regressions decisive. For Claude the figures are 9 of 66 and 24 of 64 (27
  under first-valid). No decisive consensus is reversed. Stage C adds alternative sentence text for 41 regressions, so
  C-associated changes are not a pure representation effect.
- Claude is more decisive than Grok at every stage. This difference is large and does not depend on
  the selection choice. Category shares depend on the adjudicating family.

## 5. Uncertainty that must be disclosed with any use of these numbers

The full list is in `corrections_v2/deviation_review/DEVIATION_ASSESSMENT_2026-09-28.md`, section
"Uncertainty that must be disclosed".
Briefly:

- the retry-cap breaches and concurrent runners;
- 13 records whose launch status is `unknown`;
- the first-valid violations and the selection judgment calls above;
- a collision record deleted during `p02_C_j2_b02` slot 3, for which only transcript evidence
  survives;
- template text in failed-attempt records that is not evidence;
- a CRLF→LF restoration of 29 routing files, accepted only where the bytes reproduce the recorded
  hash;
- the post-judgment timing of every selection in this note.
