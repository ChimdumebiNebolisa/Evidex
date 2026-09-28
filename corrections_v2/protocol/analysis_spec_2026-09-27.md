# Post hoc correction protocol — 2026-09-27, v2

This is a **post hoc correction protocol**, written after inspection of historical
results and evidence defects. It is NOT a preregistration of the original study,
nor an independent confirmatory analysis. It fixes the analysis before fresh
judgments. Proposed taxonomy requires coauthor review; retain that qualification
in all outputs. Do not interpret descriptive judge categories as causes of GPT
errors, and do not relabel FEVER.

## Freeze and amendment

`python corrections_v2/analysis_pipeline.py freeze-spec` verifies historical and
prepared inputs, refuses a new freeze if judgment outputs/execution records
exist, and writes an append-only UTC-dated `.freeze.json` next to this document.
It pins this specification, the handoff, record template, executed analysis code,
taxonomy code, model locks, rubrics, historical baseline and initial manifest.
The freeze excludes itself. Runtime rejects changed specification/code. A later
change requires an explicit dated amendment and separately named protocol/results;
never replace this freeze or claim that a post-judgment amendment preceded data.
Git HEAD alone is not implementation identity; file hashes pin local edits.

## Data, denominators and exclusions

- Original behavior: correct-to-wrong GPT transitions are unchanged. Historical
  40,000 predictions and +7.35/+10.87 pp gains are preserved, not re-estimated
  from judge labels. NLI diagnostics are frozen historical covariates: no new NLI,
  embeddings, retrieval or model inference belongs to this offline pipeline.
- Primary Grok: 1,060 of 1,061 diagnostic claims, five C judgments each, 55 jobs.
  Exclude only the already provider-filtered `SA-000352`; no retry or imputation.
  Keep historical sampled cohort labels (regression/resistant/rescue/robust).
  This diagnostic sample is not representative of all 10,000 claims.
- Primary Claude full: all 226 unique regression claims, five C judgments each,
  15 jobs. Cross-family comparisons pair the same 226 claims, never independent
  samples or all 1,060 Grok claims against the 226 Claude claims. Shared/model-
  specific subgroups remain 40 both, 75 GPT-5.4-only, 111 mini-only.
- Required total: 70 jobs / 6,430 fresh C judgments. The optional fixed historical
  residual cohort is 231 claims / 1,155 judgments / 15 jobs; analyze separately
  as fixed-cohort sensitivity, not as the newly selected corrected residual set.
- New residual: select corrected **raw** Grok C in {Ambiguous, Unresolved}, after
  Grok C outputs/provenance are frozen. Let size be R. Sort source IDs, shuffle
  with NumPy seed 20260823, assign new opaque V2R IDs, batch 77, five fresh Claude
  contexts per batch: 5R judgments, `5 * ceil(R/77)` jobs. Overlap with earlier
  panels does not authorize reuse. R=0 means no jobs and no conditional estimate.
- Resolver: independently select non-high-consensus corrected Grok C; K records,
  batches of 100 and one locked Grok resolver context per batch. Anonymize each
  item's ratings using seed 20260829, neutral r1..r5 and shuffled display order;
  historical resolver preparation withholds reasons (empty string). Resolver
  outcomes never replace raw consensus, taxonomy, or primary residual selection.
  A/B resolver artifacts stay historical; no full legacy resolver-gated pipeline
  completion claim until the separate C resolver results/provenance exist.

## Output ingestion, missingness and provenance

Require every expected item/judge slot exactly once, correct order, stage and
judge ID, supported schema values, integer confidence 0–100, nonempty reasons,
valid issue flags and exact packet hashes. Reject missing, duplicate, malformed
or unexpected records. No partial-panel scientific estimates, silent complete-
case analysis, copied historical C, or imputed judgments. Missing/invalid selected
outputs or provenance produce explicit incomplete/pending status and nonzero exit.
The default primary analysis waits for both required panels; an explicitly named
Grok-only analysis may finish independently to prepare subsequent jobs.

Retain exact raw response and routing evidence, hashes, requested/resolved slug,
provider version if exposed (otherwise explicit not-exposed limitation), Cursor
version, UTC start/end, unique context ID, packet/output hash, settings, operator
and human reviewer. Version metadata being unavailable is a recorded limitation,
not permission to assume a model identity. A resolved slug that cannot be
verified to the historical lock blocks acceptance. Recorded review is not
independent provider attestation. Capture every attempt, at most three total;
accept the first schema-valid response, never retry because of its verdicts.
No edit to records is allowed when extracting JSON from a raw fenced response.
Freeze complete selected raw outputs and provenance before any label/cohort join.

## Consensus and the historical tie ambiguity

Five judges per item; evaluation order is numeric judge slot 1,2,3,4,5, matching
historical configuration/file traversal. The historical `Counter.most_common(1)`
selects the first encountered verdict on modal ties. Preserve this implementation:

1. At least four Supported or four Refuted -> that label, `high_consensus`.
2. Otherwise, modal Ambiguous with at least two votes -> Ambiguous,
   `ambiguous_majority`.
3. Otherwise, at least three sufficiency values in {partial_or_ambiguous,
   probably_insufficient, clearly_insufficient} -> Ambiguous,
   `ambiguous_weak_sufficiency`.
4. Otherwise -> Unresolved.

A 2 Supported / 2 Ambiguous / 1 Refuted split with fewer than three weak ratings
can be Ambiguous or Unresolved depending on which tied mode appears first. Do
not silently promote Ambiguous or change this to majority voting. Record modal
tie, selected mode, judge order, label sensitivity and all labels attainable by
reordering tied modes. Those sensitive labels are both nondecisive, so primary
nondecisive proportions, v2 categories and residual membership are unaffected;
exact-label confusion/agreement and transitions can differ and must expose flags.
Modal sufficiency likewise follows fixed order. Tests compare all 243 verdict
patterns (with representative weak-rating counts) to the historical function.

Historical A/B: load immutable raw records, normalize numeric judge suffixes to
slots, collapse only identical historical duplicates in sorted file order, reject
conflicts; require all five slots and reproduce frozen A/B consensus. Record
source paths/raw hashes and baseline verification. Retention rests on identical
visible A/B inputs and documented stage isolation, NOT independently verified
provider transcripts. Numeric-slot per-judge transitions compare replicate slots,
not a continuing judge conversation or stable individual identity across stages.

## Proposed descriptive taxonomy and transitions

Use `silver_adjudication_v1/src/taxonomy_v2.py::classify` unchanged, with FEVER gold,
cohort, retained A/B, fresh C, and corrected evidence's `c_adds_sentence_text`:

1. Nondecisive C -> final_nondecisive.
2. Decisive C disagreeing with FEVER -> decisive_judge_fever_disagreement.
3. Gold-agreeing C with decisive reversal or loss of decisiveness -> nonmonotonic_judge_path.
4. Otherwise A gold-agreeing -> sentence_only_gold_agreeing.
5. Otherwise title resolution -> title_disclosure_gold_agreeing.
6. Otherwise -> additional_evidence_gold_agreeing if C adds sentence text;
   structured_disclosure_gold_agreeing if it does not.

Keep first decisive/gold-agreeing stage, reversals, lost decisiveness, title/C
resolution and A-only utilization-compatible fields. Nondecisive FEVER agreement
is null, not disagreement; FEVER-agreement rates condition on decisive labels.
No invented broad mapping to legacy mechanism categories. C resolution is not
automatically a formatting effect because C can add information.

Compute claim-level A/B/C matrices, per-judge-slot verdict changes, confidence
deltas and sufficiency improvements, and within-panel pair agreement, Fleiss
kappa and nominal Krippendorff alpha. Historical all-single-category convention
for within-panel kappa/alpha is 1; cross-family Cohen kappa with constant margins
is undefined/null. Export tie diagnostics alongside consensus.

## Statistical analyses (all post hoc)

Unit = claim, not five pseudo-independent judgments. Rates include numerator
and actual denominator; empty strata yield null/not-estimable, never zero rates.
Use 2,000 percentile bootstrap resamples, NumPy fixed seeds, 95% intervals; also
Wilson 95% intervals for descriptive rates. Grok Q rates use historical seed
20260822. Descriptive v2 category rates use 20260913 + category index + 1;
stage ambiguity uses 20260913 + 21 + stage index; other rates use 20260822.
Cross-family exact-category agreement uses 20260913 + 41. Residual rates use
20260824, decisive FEVER agreement 20260829. Sort claim IDs/source IDs before
sampling; exact bootstrap realizations need not equal old output row-order draws.

Recompute original Grok Q1–Q12 endpoint families with stated corrections:

- Q1: A nondecisiveness by cohort; regression versus robust Fisher/OR.
- Q2/Q3: title/C resolution by cohort and regression versus robust Fisher/OR.
- Q4: A/C nondecisiveness, resistant versus robust and versus regression.
- Q5: shared versus model-specific regression title/C resolution and C nondecisiveness.
- Q6: A/B/C nondecisiveness all/regression; paired stage tests use the original
  asymptotic continuity-corrected McNemar formula (zero discordance -> undefined).
- Q7/Q8: A–B/B–C consensus change rates all/regression.
- Q9: high-consensus C decisiveness, plus separately FEVER-agreeing/disagreeing C.
  Do not describe a decisive FEVER-disagreeing judgment as clearly warranted gold.
- Q10: title, structure-only, and added-evidence v2 categories separately by
  regression/resistant/robust. This replaces, not silently equates to, the legacy
  pooled representation-sensitive endpoint.
- Q11: C nondecisiveness all/regression.
- Q12: A/C nondecisiveness versus both frozen NLI-disagreement indicators;
  historical chi-square with default continuity correction and phi. Constant
  margins -> not estimable. No new NLI results.

Fisher tests are two-sided. Historical Grok OR floors b/d at .5 and uses .5 floors
for CI standard error; when a or c=0 report undefined OR/CI but retain Fisher p.
Claude shared-versus-specific OR uses its historical .5 floor on all four cells.
Do not quietly substitute a different continuity correction. One BH family for
estimable Grok Q1–Q12 p-values; report family size and undefined endpoints.

Cross-family: exact fine-category agreement, Cohen kappa, full confusion and final
label matrix; paired exact-binomial McNemar for A/B/C nondecisiveness, title/C
resolution, reversals, and each v2 category (BH across this family). Zero
discordance has exact p=1. Shared/specific C nondecisiveness ORs are a separate
two-test BH family. Descriptive rates include each cohort and both/75/111
regression strata; do not recreate obsolete broad mechanism claims.

Residual analyses: new selection and fixed-231 sensitivity are distinctly named.
Compute persistence/nondecisiveness by cohort/shared status, conditional decisive
FEVER agreement, exact cross-family label agreement, regression-versus-resistant
Fisher/OR and persistent-versus-resolved confidence Mann–Whitney U; BH over those
two exploratory tests. Resolver uses separately named outcome summaries and
raw/resolver comparison, never an alternative primary estimate by default.

## Versioned outputs and cases

Complete runs write new `results/<version>/` tables, SVG plots, raw consensus/tie
diagnostics, retained-A/B provenance, representative cases and an exact-byte
artifact manifest, linked to protocol/judgment freezes. No historical output is
overwritten. Work-in-progress uses a hidden `.incomplete` directory; only a
verified final artifact manifest denotes completion. Never overwrite a completed
version. Pending calls create no estimate/table/plot directory.

Representative cases: first sorted source ID in each v2 category and first
order-sensitive C case per primary panel, with corrected packet and labels;
conditional panels use first sorted ID per final label. No selection based on
effect size, persuasive narrative or a preferred conclusion. Plot category
proportions and transition counts; conditional plots show outcomes only after
complete fresh selected-panel data.

Frozen original behavioral analyses remain referenced historical results, not
new corrected-packet findings. No updated manuscript claim is authorized merely
by infrastructure success. Execution availability, coauthor review, provenance
review and substantive scientific interpretation remain human handoff gates.
