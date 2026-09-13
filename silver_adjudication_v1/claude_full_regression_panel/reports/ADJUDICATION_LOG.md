# Claude full-regression panel log

Running record of setup, execution, retries, deviations and null findings —
anti-cherry-picking documentation.

## Setup (2026-09-13)

- Branch `research/evidex-claude-full-regression-panel-v1` created from `main`
  @ `ade9ff6`. No frozen experiment was modified.
- Model lock: `claude-opus-5-thinking-high` for all five judges, all stages.
  Auto/inherit and the Grok/GLM slugs are refused in code.
- Cohort independently recomputed from `analysis_v2` as
  `transition == "correct_to_wrong"` for either GPT model: **n = 226**
  (40 both / 75 `gpt-5.4` only / 111 `gpt-5.4-mini` only), identical claim-id
  set to the frozen shared cohort manifest.
- Opaque IDs `CF-000001`–`CF-000226`, seed 20260913. Private map in
  `data/id_map.csv`.
- Stage A/B/C evidence reused verbatim from the shared blinded stage files; no
  new retrieval, no browsing.
- Rubric reused byte-identically from `../prompts/judge_rubric.md`.
- Isolation: fresh Task subagent per `(judge, batch, stage)`; batch size 77
  (3 batches per judge per stage); packet-only I/O.

## Deviations from protocol

1. **Judge-facing paths moved to a neutral directory (2026-09-13).** The first
   Stage A batch-01 wave was launched with packet and output paths inside
   `silver_adjudication_v1/claude_full_regression_panel/…`. The panel directory
   name contains the word that names the cohort selection criterion, so those
   paths were themselves a blinding leak — caught by
   `TestBlinding.test_no_prohibited_text_in_judge_facing_metadata`. The five
   delivered files (5 × 77 = 385 valid judgments) were **quarantined unread**
   into `cache/discarded/pre_blinding_fix_stage_a/` with their sha256 hashes and
   a written reason, and batch 01 was rerun with all judge-facing paths under
   `silver_adjudication_v1/blind_io/`. No verdict from the discarded wave was
   inspected, and the decision applied to the whole batch rather than to
   selected items. The blinding condition is therefore uniform across all 226
   items. Cost: 385 judgments of Claude capacity.
   Note: the frozen Claude residual panel carries the same path exposure
   (`claude_residual_panel`); it is not retro-fixed because frozen experiments
   are not modified.
2. **Judge IDs are `claude_full_judge_*`** rather than the residual panel's
   `claude_judge_*`, so that the two Claude experiments can never be conflated
   in analysis. The `judge_id` field itself is unchanged.
3. **No resolver.** As in the Claude residual panel, the primary result is raw
   five-judge consensus. The Cursor/Grok panel additionally ran a same-family
   resolver on non-high-consensus items; its consensus labels — which are what
   the taxonomy consumes — are unaffected by that resolver, so the taxonomy
   comparison remains like-for-like. Recorded as a deliberate scope choice.
4. **Duplicate Stage B runs, resolved by a content-independent tie-break.**
   Recovery from the capacity interruption overlapped, so three `(judge, batch)`
   units — `claude_full_judge_4` batches 01, 02 and 03 — were adjudicated twice
   by two independent `claude-opus-5-thinking-high` subagent runs. Both copies
   are legitimate Claude output, but the design permits exactly one judgment per
   `(stage, judge_id, item_id)`. The rule applied was **first ingested wins**:
   purely temporal, decided without reading either copy's verdicts and without
   comparing them, so it cannot express a preference for one result over the
   other. The superseded bytes are preserved with hashes and a written reason in
   `cache/discarded/duplicate_rerun_superseded_stage_b/`. The duplication was
   caught rather than silently absorbed because `run_judges.ingest` refuses to
   overwrite an already-ingested file whose bytes differ.

## Judging

### Stage A (sentence-level evidence only) — complete, frozen

- 15 packets (5 judges × 3 batches of 77/77/72), one fresh Task subagent each,
  all on `claude-opus-5-thinking-high`.
- Launched in three waves of five to stay inside the background-subagent
  concurrency limit. Wave order was judge-major only for scheduling; item order
  inside every packet is the same fixed shuffled cohort order for all judges.
- Delivered: 226/226 valid records per judge, 1130 total. No malformed files,
  no schema rejections, no retries needed, no missing items.
- Exact launch text for every packet archived under
  `blind_io/launch_prompts/stage_a/`.
- Frozen to `freezes/freeze_stage_A.json`; integrity re-verified after writing.

### Stage B (adds page titles) — in progress after Stage A freeze

- Stage B packets were generated only after `freeze_stage_A.json` verified, so
  no judge could see Stage B evidence before Stage A was locked.
- Fresh subagents again: no judge context carries over from Stage A, matching
  the Cursor/Grok convention of fresh contexts between stages.
- First Stage B wave (15 packets) launched from the prior session. Several
  packets completed a Claude `Write` of the inbox file and then the parent
  session hit `Other Models usage limit reached / Switched to grok-4.6`.
  **No Grok (or other) substitution was accepted.** Packets that never wrote
  an inbox file were left missing. Packets whose Claude write landed before
  the limit error were kept.
- Ingested 8 valid Stage B files (schema-valid, expected counts):
  judges 1 and 2 complete (226/226 each); judge 3 batches 02+03 (149/226);
  judges 4 and 5 empty.
- Resume (this session) relaunched five remaining packets on
  `claude-opus-5-thinking-high` only. All five failed immediately with
  `Other Models usage limit reached / Switched to grok-4.6`. **Grok was
  refused.** No inbox file was written for any of those five packets.
  Judge 5 batches 02 and 03 were never relaunched.
- **Model provenance of the limit-error packets was verified from evidence, not
  assumed.** Three delivered files (`judge_2` batches 01 and 03, `judge_3` batch
  03) came from subagents whose run *ended* with
  `Other Models usage limit reached / Switched to grok-4.6`, which raised the
  question of whether the fallback model had written any of those bytes. Their
  subagent transcripts were inspected: each contains only Claude assistant
  turns — read packet, adjudicate, `Write` the inbox file with full contents —
  followed by `turn_ended status=error` carrying the limit message. No
  `grok-4.6` turn exists in any of the three transcripts, so the switch applied
  to a continuation that never happened and every byte was written by
  `claude-opus-5-thinking-high`. The files were therefore kept.
  These three were briefly quarantined under a precautionary
  "unverifiable provenance" tag before that check was run; the quarantine was
  reverted once the transcripts established Claude authorship, since discarding
  valid Claude work would itself violate the no-discard rule. The restored
  files are byte-identical to the ingested copies (`ingest` refuses any file
  that differs from an already-ingested one, and reported no change).
- **Interim STOP.** Capacity exhausted at 601/1,130. Valid completed judgments
  preserved; remainder recorded in `freezes/STOPPING_POINT.json` and
  `freezes/missing_work_manifest.json`. Nothing was discarded and no model was
  substituted.
- **Resumed same day once Claude capacity returned.** The seven outstanding
  packets (judge 3 batch 01; judge 4 batches 01–03; judge 5 batches 01–03)
  were relaunched on `claude-opus-5-thinking-high` from the archived prompts
  in `blind_io/launch_prompts/stage_b/`. All seven delivered full counts.
  The 601 judgments carried over from the interrupted wave were not rerun and
  not re-inspected; they are the same files ingested before the stop.
- Stage B complete: 226/226 valid per judge, 1,130 total, no malformed files.
  Frozen to `freezes/freeze_stage_B.json`; integrity re-verified.

### Stage C (adds reconstructed structured evidence) — complete, frozen

- Stage C packets were generated only after `freeze_stage_B.json` verified.
  `write_packets` refuses to build a stage whose predecessor is unfrozen, so
  the progressive-disclosure ordering is enforced in code, not by convention.
- 15 packets, fresh Task subagent each, all `claude-opus-5-thinking-high`.
  Launch text archived under `blind_io/launch_prompts/stage_c/`.
- Delivered: 226/226 valid per judge, 1,130 total. No malformed files, no
  schema rejections, no retries, no missing items.
- Frozen to `freezes/freeze_stage_C.json`; integrity re-verified.

## Completeness (complete 2026-09-13)

- Stage A: 1,130/1,130 valid, frozen, integrity re-verified.
- Stage B: 1,130/1,130 valid, frozen, integrity re-verified.
- Stage C: 1,130/1,130 valid, frozen, integrity re-verified.
- Panel total: **3,390/3,390 valid**; `missing_work_manifest.json` reports
  `complete: true`, 0 missing.
- Pre-unblinding manifest `freezes/freeze_manifest.json` written and verified
  unchanged *before* any join to regression, GPT, FEVER or Grok metadata.
  Pre-unblinding commit: `adb104f`.
- Consensus for all three stages was computed under blinding, before unblinding.

## Post-unblinding

- Unblinding performed only after freeze verification passed. Taxonomy applied
  programmatically by the shared rule function; no manual classification, no
  rule edits after seeing results.
- `STOPPING_POINT.json` is retained as a record of the interruption. It
  describes the interim state and is superseded by the completeness section
  above.

## Null findings / notes

- **Neither judge family ever reversed a decisive consensus** under additional
  disclosure: 0/226 reversals after titles and 0/226 after structured evidence,
  in both the Claude and the Grok panel. Progressive disclosure resolves
  ambiguity; it does not flip Supported↔Refuted. Reported because it is a clean
  null that constrains how the representation-sensitive category should be read.
- **Claude produced zero `silver_title_context_sensitive` items, and so did Grok
  on this cohort.** Both panels' representation-sensitive slices are entirely
  structured-evidence-sensitive. The finer title-context category is retained in
  the taxonomy for comparability with the shared pipeline but is empty here in
  both families, so no title-specific claim can be made either way.
- **No item landed in `other`/`silver_unresolved` in either family.**
- **The panel is not internally noisy**, so the cross-family gap cannot be
  attributed to Claude judge instability: Fleiss κ = 0.897/0.904/0.884 at
  A/B/C, and per-judge Ambiguous rates span only 22.1–30.1% at Stage A.
- The retained `STOPPING_POINT.json` and the interim capacity stop are recorded
  above rather than deleted, so the interruption remains auditable even though
  the panel later completed.
