> Publication navigation copy: the eight original local-file links now point to the pinned public results bundle. [Original report bytes](ACTUAL_RESULTS.original.txt) are retained unchanged; all result text below is unchanged.

# Evidex full3 actual results

Analysis and integrity verification: **PASS**. Frozen analysis exited 0 at 2026-10-17 23:35:33 UTC (6:35 pm Central); output verification passed at 23:35:42 UTC. Collection completed at 13:42:03 UTC. No paid calls were made during offline finalization.

Across three repetitions, adding the supplied gold evidence (A to B) increased accuracy by 7.55 percentage points for gpt-5.4 and 10.79 points for gpt-5.4-mini. Adding the evidence-only instruction (B to C) changed accuracy by +0.02 and +0.17 points, respectively; both repeated-summary 95% intervals include zero. Evidence rescued more errors than it introduced, but introduced some regressions. These comparisons apply to the frozen claim set, prompts and provider occasion.

## Design and denominators

10,000 claims; 9,855 claim-text clusters; two models; three conditions; three repetitions: 180,000 planned and valid calls. First-pass cells contain 10,000 calls; repeated cells contain 30,000 calls, reduced within claim for uncertainty. The repeated summary includes repetition 1 and is not an independent replication. Label strata have the original 50/50 weights. All confidence intervals below are the unchanged frozen 2,000-draw joint claim-text-cluster bootstrap intervals; no bootstrap was rerun.

- A: claim only, generic classification instruction.
- B: claim plus gold evidence, same generic classification instruction.
- C: claim plus gold evidence, with “based only on the evidence provided” added.

Returned snapshots: gpt-5.4-2026-03-05 and gpt-5.4-mini-2026-03-17 (90,000 calls each).

## Accuracy

| Summary | Model | Condition | Correct / assigned (all valid) | Accuracy % | 95% interval % |
|---|---|---|---:|---:|---|
| First pass | gpt-5.4 | A | 8,858 / 10,000 | 88.58 | 87.95 to 89.20 |
| First pass | gpt-5.4 | B | 9,617 / 10,000 | 96.17 | 95.77 to 96.53 |
| First pass | gpt-5.4 | C | 9,622 / 10,000 | 96.22 | 95.83 to 96.61 |
| First pass | gpt-5.4-mini | A | 8,490 / 10,000 | 84.90 | 84.19 to 85.60 |
| First pass | gpt-5.4-mini | B | 9,545 / 10,000 | 95.45 | 95.04 to 95.86 |
| First pass | gpt-5.4-mini | C | 9,570 / 10,000 | 95.70 | 95.30 to 96.07 |
| Three repetitions | gpt-5.4 | A | 26,584 / 30,000 | 88.61 | 88.01 to 89.22 |
| Three repetitions | gpt-5.4 | B | 28,848 / 30,000 | 96.16 | 95.77 to 96.53 |
| Three repetitions | gpt-5.4 | C | 28,853 / 30,000 | 96.18 | 95.79 to 96.56 |
| Three repetitions | gpt-5.4-mini | A | 25,419 / 30,000 | 84.73 | 84.04 to 85.43 |
| Three repetitions | gpt-5.4-mini | B | 28,655 / 30,000 | 95.52 | 95.12 to 95.89 |
| Three repetitions | gpt-5.4-mini | C | 28,706 / 30,000 | 95.69 | 95.29 to 96.06 |

## Paired regressions and rescues

Regression means correct in the left condition and wrong in the right; rescue means wrong to correct. Rates use all assigned pairs, not only initially correct or incorrect cases. All pairs are valid and classified. Accuracy change equals (rescues minus regressions) / assigned pairs. The supplement retains both-correct and both-wrong counts.

| Summary | Model | Pair | Assigned pairs | Regressions (%, 95% interval) | Rescues (%, 95% interval) | Accuracy change pp (95% interval) |
|---|---|---|---:|---|---|---|
| First pass | gpt-5.4 | AB | 10,000 | 98 (0.98; 0.79 to 1.18) | 857 (8.57; 8.03 to 9.12) | 7.59 (7.01 to 8.19) |
| First pass | gpt-5.4 | BC | 10,000 | 41 (0.41; 0.29 to 0.54) | 46 (0.46; 0.33 to 0.60) | 0.05 (-0.14 to 0.24) |
| First pass | gpt-5.4 | AC | 10,000 | 108 (1.08; 0.89 to 1.29) | 872 (8.72; 8.17 to 9.28) | 7.64 (7.04 to 8.22) |
| First pass | gpt-5.4-mini | AB | 10,000 | 145 (1.45; 1.23 to 1.69) | 1,200 (12.00; 11.37 to 12.62) | 10.55 (9.87 to 11.26) |
| First pass | gpt-5.4-mini | BC | 10,000 | 66 (0.66; 0.50 to 0.81) | 91 (0.91; 0.74 to 1.10) | 0.25 (0.01 to 0.51) |
| First pass | gpt-5.4-mini | AC | 10,000 | 147 (1.47; 1.24 to 1.71) | 1,227 (12.27; 11.65 to 12.90) | 10.80 (10.11 to 11.50) |
| Three repetitions | gpt-5.4 | AB | 30,000 | 301 (1.00; 0.82 to 1.20) | 2,565 (8.55; 8.03 to 9.08) | 7.55 (6.95 to 8.14) |
| Three repetitions | gpt-5.4 | BC | 30,000 | 139 (0.46; 0.34 to 0.59) | 144 (0.48; 0.36 to 0.62) | 0.02 (-0.16 to 0.20) |
| Three repetitions | gpt-5.4 | AC | 30,000 | 336 (1.12; 0.93 to 1.33) | 2,605 (8.68; 8.15 to 9.23) | 7.56 (6.98 to 8.14) |
| Three repetitions | gpt-5.4-mini | AB | 30,000 | 426 (1.42; 1.21 to 1.63) | 3,662 (12.21; 11.61 to 12.82) | 10.79 (10.13 to 11.44) |
| Three repetitions | gpt-5.4-mini | BC | 30,000 | 200 (0.67; 0.53 to 0.80) | 251 (0.84; 0.69 to 0.99) | 0.17 (-0.02 to 0.37) |
| Three repetitions | gpt-5.4-mini | AC | 30,000 | 449 (1.50; 1.28 to 1.73) | 3,736 (12.45; 11.85 to 13.06) | 10.96 (10.31 to 11.62) |

## Repeat variability

Identical-prompt disagreement averages the three unordered repeat-pair label disagreements within each claim. Its denominator is 10,000 complete claims per cell (30,000 repeat pairs); it is not the proportion of claims with any disagreement. Both are shown.

| Model | Condition | Claims with any disagreement / 10,000 | Disagreeing repeat pairs / 30,000 | Mean disagreement % (95% interval) |
|---|---|---:|---:|---|
| gpt-5.4 | A | 100 | 200 | 0.67 (0.54 to 0.80) |
| gpt-5.4 | B | 23 | 46 | 0.15 (0.10 to 0.22) |
| gpt-5.4 | C | 29 | 58 | 0.19 (0.13 to 0.26) |
| gpt-5.4-mini | A | 350 | 700 | 2.33 (2.09 to 2.58) |
| gpt-5.4-mini | B | 107 | 214 | 0.71 (0.59 to 0.85) |
| gpt-5.4-mini | C | 98 | 196 | 0.65 (0.52 to 0.79) |

The frozen excess-loss comparison subtracts the mean directional correct-to-wrong loss across the six ordered repeats of the left prompt from the paired-condition regression rate. All 10,000 claims are complete.

| Model | Pair | Excess loss pp (95% interval) | Claims regressing in all 3 repetitions / 10,000 |
|---|---|---|---:|
| gpt-5.4 | AB | 0.67 (0.48 to 0.87) | 87 |
| gpt-5.4 | BC | 0.39 (0.27 to 0.51) | 32 |
| gpt-5.4-mini | AB | 0.25 (0.02 to 0.49) | 99 |
| gpt-5.4-mini | BC | 0.31 (0.18 to 0.44) | 27 |

Persistence over three calls does not establish a stable individual causal effect. Full per-claim repeat outcomes and the independently checked 0/1/2/3 regression and rescue histograms are retained in the supplement.

## Coverage and integrity

180,000 unique planned jobs, admissions, substantive responses and valid final outcomes. Zero terminal failed, invalid, uncertain, missing or pending jobs; zero duplicate admissions, response IDs or raw-response hashes; no unclassified analysis pairs. All 180,000 jobs used exactly one actual request. Eight earlier recovery-only attempt directories contain no API request; ordinal 2 is the first actual call for those jobs. These are not API retries.

720,008 attempt artifacts were inventoried and hashed; all 165,792 sealed baseline artifacts were preserved. Every saved request/settings hash, raw receipt hash, frozen interpretation, plan/run identity and old/new operational seal passed the completed integrity check. Final database backup, failed/partial/recovery records and the original Windows-interrupted analysis records remain preserved. The offline recovery changed no scientific source or settings.

## Recorded usage and cost

| Model | Calls with usage | Prompt tokens | Completion tokens | Reported cached / reasoning tokens | Frozen-rate cost USD |
|---|---:|---:|---:|---:|---:|
| gpt-5.4 | 90,000 | 6,444,021 | 429,827 | 0 / 0 | 22.55745750 |
| gpt-5.4-mini | 90,000 | 6,444,021 | 532,690 | 0 / 0 | 7.23012075 |

Total: **12,888,042 prompt tokens; 962,517 completion tokens; $29.78757825** using the frozen undiscounted input/output rates (per million: gpt-5.4 $2.50/$15.00; mini $0.75/$4.50). Cache and reasoning fields were present and zero on all 180,000 receipts. Completion usage already includes any reasoning tokens; none were added twice. No saved attempt is missing usage, and no uncertain transmission remains in this ledger. No cache discount was applied. This is independently reconciled recorded usage and frozen-rate arithmetic, **not an independently reconciled provider invoice**. The cumulative $35 guard was preserved.

## Limits and unresolved issues

No unresolved integrity or accounting mismatch was found. Provider invoice reconciliation remains outside these recorded artifacts. Intervals describe claim-text-cluster sampling uncertainty on this frozen set and provider occasion; they do not measure changes across provider snapshots or dates. The selected historical-case summaries and recorded historical-label comparisons remain in the frozen summary; they cannot recreate or identify undocumented historical model changes and are not the primary full-set comparison. No claim that C reliably improves on B is supported by the repeated accuracy intervals, which include zero. No new inference, invalid-response replacement, redesign or scientific reanalysis was performed.

## Evidence and checks

- [Frozen summary](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/summary.json.gz)
- [Frozen observations](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/observations.csv.gz)
- [Frozen provenance](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/provenance.json.gz)
- [Analysis verification](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/ANALYSIS_VERIFICATION.json)
- [Completed integrity/accounting](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/INTEGRITY.json)
- [Independent outcomes](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/OUTCOMES.jsonl.gz)
- [Independent comparison verification and numeric supplement](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/RESULTS_VERIFICATION.json)
- [Report-generation/check source](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17/snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/finish_actual_results.py)

Output hashes were rechecked against ANALYSIS_VERIFICATION.json. Independently checked first-pass, repeated and selected historical accuracy/pair numerators and denominators against OUTCOMES.jsonl, plus every full-set and historical per-claim repeat record and aggregate point estimate. Frozen confidence intervals were transcribed without recomputation.

What changed: added this report and independent comparison verification. Files changed: ACTUAL_RESULTS.md, RESULTS_VERIFICATION.json and finish_actual_results.py; original artifacts and frozen analysis outputs were preserved. Verification run: read-only outcome/summary comparisons and recorded output/outcome hash checks. Result: PASS. Remaining uncertainty: provider invoice reconciliation and the stated scope of statistical inference.
