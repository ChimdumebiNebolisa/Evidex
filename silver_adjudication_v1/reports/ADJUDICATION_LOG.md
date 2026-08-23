# Adjudication Log (silver v1)

Running record of panel setup, execution, retries, deviations, and null
findings — anti-cherry-picking documentation.

## Panel setup (2026-08-22)

- 5 isolated GLM-5.3 judge subagents (judge_1..judge_5), each a FRESH agent
  context per batch; no judge sees another judge's output, consensus,
  FEVER labels, GPT predictions, transitions, NLI outputs, similarity, or
  cohort type. Judges read only `prompts/judge_rubric.md` + their item range
  of the stage's blinded JSONL.
- Model: GLM-5.3 (environment general-purpose subagent; same family for ALL
  judges — within-family agreement only).
- Rubric version: `prompts/judge_rubric.md` v1 (2026-08-22), unchanged
  across judges and stages.
- Batch size: 100 items (11 batches/stage; batch 11 = 61 items).
- Item IDs: SA-000001..SA-001061, seeded shuffle (seed 20260822) of cohort
  claim_ids; ID-neutrality validated (chi-square across ID halves, p>0.01).

## Execution environment notes

- Background subagent concurrency limit observed: ~2-3 simultaneous agents;
  launches beyond the limit fail immediately ("user concurrency limit
  exceeded") without consuming judge state. Failed launches are relaunched
  with identical blinded inputs (this is launch retry, not judgment retry).
- One transient "Model request failed" on judge_1 batch 01; relaunched,
  completed. Recorded as retry #1 for judge_1.

## Judgment retries (schema failures requiring re-prompt)

(none so far)

## Stage freezes

- Stage A: FROZEN 2026-08-22 (all 5 judges x 1060 items valid; manifest
  `data/derived/freeze_stage_A.json`; integrity re-verified in this session).

## Deviations from protocol

- None. Stage C structured evidence reconstructed from the official FEVER
  wiki archive (fever.ai, https-only, host-validated) per user decision;
  alternative-set sentence text recovered for 506/508 referenced sentences
  (2 pointer-only due to missing pages in the archive).
- Item SA-000352 excluded (provider-side content filter causes an empty
  model response in every GLM subagent request that includes it, isolated
  by bisection). Excluded from expected items in run_judges; never judged in
  any stage; consensus computed over the remaining 1060 items; documented in
  `data/derived/provider_filtered.json`; unblinding joins its cohort
  metadata only (no silver label). Recorded as a deviation on 2026-08-22.

## Null findings / notes

- (pending)

## Judging session 2 (Stage A continuation)

- judge_2 batch_06 (SA-000501..0600): OK, 100 valid.
- judge_1 batch_06 (SA-000501..0600): OK, 100 valid.
- judge_3 batch_04 (SA-000401..0500): FAILED (provider "Model request failed", empty response). Retry 1 launched with same blinded range + two-part write guidance.
- judge_4 batch_04 (SA-000401..0500): launched.
- judge_5 batch_04 (SA-000401..0500): launched.

## Judging session 3 (Stage B, 2026-08-22 evening)

- Resumed Stage B at 13/55 batch files (judges 1-3 at 300/1060, judges 4-5
  at 200/1060).
- DISCOVERED: a second orchestrating session is concurrently working the
  same Stage B queue (batch_04a/b split files appeared for judges this
  session never launched). Coordination: this session works backward from
  batch 11 using `_s2`-suffixed output filenames; the shared
  `judgments/stage_b/*_missing.json` files (written by
  `run_judges.py status`) are the coordination channel. No file collisions;
  item-level dedupe in aggregation handles any overlap.
- Launch retries this session (concurrency-limit failures, no judgment
  state consumed): judge_4 b03 x2, judge_1 b04 x2.
- judge_5 batch_03: agent reported "Model request failed" AFTER writing a
  complete valid file (100 records) — file kept, batch complete.
- judge_2 batch_04b appeared as malformed mid-write from the concurrent
  session; left alone to complete.

## Infrastructure fixes (pre-aggregation, 2026-08-22)

- Fixed 2 broken unit tests (missing assertEqual arg; run_judgers typo);
  rewrote the unblinding-gate test to be deterministic (temp-dir manifest
  absence must raise; existing manifests must verify).
- Implemented missing `src/verify_headlines.py` (independent recomputation
  of headline numbers from frozen artifacts + presence check in reports +
  freeze-hash recheck; registry `reports/HEADLINES.json`).
- `src/join_analysis_v2.py`: implemented `--freeze-only`; freeze_silver now
  refuses to freeze until resolver outputs are complete for all stages and
  agreement tables exist; manifest extended to hash agreement tables;
  unblind_join now enforces the resolver-completeness gate.
- `src/resolve_disagreements.py`: fixed `validate` CLI invocation (was
  treating the subcommand as a stage name).
- `run_all.py`: agreement stage moved before freeze_silver.
- No changes to prompts/, blinded data, or any frozen artifact.

## Cursor panel branch (2026-08-23)

- Created `research/evidex-cursor-silver-adjudication-v1` from
  `research/evidex-silver-adjudication-v1`. `main` was not modified.
- Frozen GLM-5.3 Stage A remains immutable (independent silver warrant audit).
  Partial GLM Stage B is preserved for provenance and excluded from Cursor
  progressive-disclosure analyses.
- New namespace `silver_adjudication_v1/cursor_panel/` with locked model
  `cursor-grok-4.6-high-fast` for all five Cursor judges, all stages, and the
  resolver. `--panel cursor` remaps outputs; GLM `judgments/` is never written.
- Do not chain GLM Stage A into Cursor Stage B/C.

## Cursor Stage A (2026-08-23)

- Model lock: `cursor-grok-4.6-high-fast` for all five isolated judges.
- Stage A complete: 5 judges x 1060 items, schema-valid, frozen at
  `cursor_panel/freezes/freeze_stage_A.json`.
- Within-Cursor-panel Stage A: pairwise agreement 89.8%, Fleiss kappa 0.846,
  consensus Refuted 403 / Supported 349 / Ambiguous 277 / Unresolved 31.
- Cross-panel Stage A replication (GLM vs Cursor; not human validation):
  modal verdict agreement 0.862, consensus agreement 0.831, ambiguity
  agreement 0.855. Cursor Stage A is more ambiguous (29.1% vs GLM 22.3%).
  Regression ambiguity is similar (GLM 41.6% vs Cursor 45.6%). Partial GLM
  Stage B was not used.

## Cursor Stage B (2026-08-23)

- Stage B complete after Stage A freeze: 5 judges x 1060 items, schema-valid,
  frozen at `cursor_panel/freezes/freeze_stage_B.json`.
- Same locked model `cursor-grok-4.6-high-fast`. No GLM Stage A chaining.
- Consensus (pre-computed): Refuted 423 / Supported 375 / Ambiguous 241 /
  Unresolved 21.

## Cursor Stage C (2026-08-23)

- Stage C launched only after Stage B freeze. Packets used existing
  reconstructed structured evidence only (no Wikipedia browse, no new
  retrieval). Pointer-only archive gaps remain as already reconstructed.
- Stage C complete: 5 judges x 1060 items, schema-valid on first write
  (batches 01-11; batch 11 = 60 items). Frozen at
  `cursor_panel/freezes/freeze_stage_C.json`. Integrity re-verified.
- Model lock unchanged. GLM Stage B partial outputs were not used.
