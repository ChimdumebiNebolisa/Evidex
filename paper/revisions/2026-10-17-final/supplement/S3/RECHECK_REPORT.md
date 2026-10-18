# Second AI coding review

All 43 original apparent reference-conflict flags were reread against the complete frozen claim, selected evidence, original local FEVER annotations and both models’ A/B/C predictions for all three repetitions. The complete HTML review and CSV retain enough text to review without opening the experiment directory. FEVER pointers are provenance; they are not extra evidence supplied to the predictors.

| Disposition of original flag | Claims |
|---|---:|
| Plausible reference/evidence conflict | 34 |
| Clear exploratory coding mistake | 2 |
| Additional context needed | 3 |
| Unresolved interpretation | 4 |

These are AI review dispositions, not confirmed reference errors. Human review is PENDING on every row. The two clear mistakes were treating one release format as exclusive of another (117129) and reading “over 1.8 million” as excluding “over 18 million” (223499). The latter are compatible lower bounds. Context and exact-versus-at-least readings account for seven other downgraded flags. All original flags and justifications remain available alongside the new assessment.

## Non-conflict sampling and rule follow-up

Master seed 20261018 selected six non-conflict distinct claims per outcome route and up to two per original feature category, independently within group without replacement, then deduplicated while retaining sampling flags: 56 claims. Together with the 43 conflicts, this is 99 complete second reviews. RECHECK_SELECTION.json records eligibility, derived SHA256 seed and every selected ID. The reviewer saw outcomes and original coding; this was the same AI assistant, not a blinded second coder.

The first full recheck exposed repeated problems in numerical-bound interpretation, negation versus sentiment/other semantic opposition, and redundant wording tags. Version 2 clarified those application boundaries before a targeted census of all 190 claims originally assigned NUM, NEG or TXT. Fifty-nine already had full review; the other 131 received targeted review with full text and prediction records available. Review coverage is therefore 230/416 distinct selected claims (258/465 selected model/claim/contrast cases). The other 186 claims (207 cases) retain their original coding without second review. No random-sample result is presented as coverage of that unchecked remainder.

The review changed 50 claim annotations: 29 reference-assessment changes and 34 feature-set changes, overlapping on 13 claims. It also standardized identity tolerance across outcomes (for example Kojol/Kajol and Hagan/Hagen). The complete decision history retains interim and final reasoning; no silent recoding or benchmark relabeling occurred. Version 2 yields 193 supports-reference, 34 apparent-conflict, 96 insufficient and 93 ambiguous claim-level assessments, denominator 416. Those totals include unchecked claims and are selected-sample descriptions, not validated population error rates.

## Files and interpretation

- REFERENCE_CONFLICT_REVIEW.html / .csv: all 43 original flags, complete text/pointers/18 predictions, old and new assessments, justifications, pending personal review.
- CODING_CHANGE_LOG.csv: every changed claim, original/revised assessment and features, scope and reason.
- TAXONOMY_CASES_v2.csv: all 465 selected cases, with original annotations retained in explicit original_* columns.
- ANNOTATION_REVIEW_COVERAGE.csv: all 416 claims; full, targeted or not-second-reviewed status.
- REGRESSION_CODEBOOK_v2.md: original codebook plus versioned clarifications.
- CATEGORY_COUNTS_v2.csv: 66 route/feature cells with case and distinct-ID denominators.
- RECHECK_SELECTION.json / TARGETED_SELECTION.json: reproducible sampling and rule-census scope.
- DECISION_HISTORY.json and TSV decision files: complete AI review history.

The legacy annotation_confidence and feature_annotation_source fields in TAXONOMY_CASES_v2.csv are preserved version-1 metadata, not independently recalibrated confidence in version 2. Use coding_version, coding_codebook_sha256, second_review_scope, original_* fields and the decision history to distinguish authority. review_status and human_review are explicit; no unrecorded personal judgment or independent agreement statistic is inferred.

Frozen benchmark labels, correctness, raw outputs, confidence intervals, request settings and sample membership did not change. A visible feature such as negation is a comparison demand, not evidence of an internal model mechanism. Stronger claims about true reference errors require personal/source adjudication. The manuscript proceeds with benchmark-relative results and these limitations, without waiting for those decisions.
