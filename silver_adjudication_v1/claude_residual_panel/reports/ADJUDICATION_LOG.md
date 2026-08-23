# Claude residual panel log

## Setup (2026-08-23)

- Branch `research/evidex-claude-residual-stagec-v1` created from
  `research/evidex-cursor-silver-adjudication-v1` @ 64d0914.
- `main` untouched (414806d).
- Model lock: `claude-opus-5-thinking-high` for all five judges.
- Isolation: fresh Task subagent per (judge, batch); packet-only I/O.
- Residual n=231 reconstructed from
  `cursor_panel/freezes/consensus_stage_C.parquet`.
- Opaque IDs `CR-000001`–`CR-000231`, seed 20260823.

## Judging

- Batch 01 (77): all five judges OK, first-try valid (first Cursor account).
- Batch 02 (77): all five judges OK, first-try valid (first Cursor account).
- Batch 03 (77): first account hit “Other Models usage limit reached”.
  Offered fallback `grok-4.6` was refused. No substitution.
- Batch 03 resumed under a **second Cursor account** because the first
  account exhausted its Claude usage allowance. Existing blinded packets
  (`cache/packets/claude_judge_*_batch_03.json`), rubric, judge IDs,
  model slug, and inference settings were unchanged. Batches 01–02 were
  not rerun. All five judges completed 77/77 on first-try valid schema.

## Completeness

- Each judge 231/231. Raw judgments 1,155. Schema retries: 0.
- Judge freeze: `freezes/freeze_judgments.json`.
- Pre-unblinding manifest: `freezes/freeze_manifest.json`.

## Consensus and analysis

- Raw consensus: Ambiguous 130 / Supported 63 / Refuted 34 / Unresolved 4.
- No resolver (primary result is raw consensus).
- Unblind and stats only after freeze verification.

## Retries

- Schema retries: 0
- Launch refusals (model lock, first account): batch 03 wave, then one
  single-judge retry of judge 1 batch 03 — both hit the usage limit.
- Second-account batch 03 launches: completed; no model substitution.
