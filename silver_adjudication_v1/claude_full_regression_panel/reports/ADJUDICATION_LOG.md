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
- **STOP.** Capacity exhausted. Valid completed judgments preserved.
  Compact remainder: `freezes/STOPPING_POINT.json`. Full item-id lists:
  `freezes/missing_work_manifest.json`.

## Completeness (stopped 2026-09-13)

- Stage A: 1,130/1,130 valid, frozen, integrity re-verified.
- Stage B: 601/1,130 valid ingested; 529 missing. Not frozen.
- Stage C: 0/1,130 (not launched; predecessor not frozen).
- Panel total: 1,731/3,390 valid.
- Stage B and C are incomplete, so consensus, taxonomy, and Grok comparison
  are **not** run. No unblinding.

## Null findings / notes

(appended)
