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

- Batch 01 (77): all five judges OK, first-try valid.
- Batch 02 (77): all five judges OK, first-try valid.
- Batch 03 (77): **not launched**. Locked model unavailable
  (usage limit). Offered fallback grok-4.6 was refused.

## Retries

- Schema retries: 0
- Launch refusals (model lock): batch 03 wave, then one single-judge
  retry of judge 1 batch 03 — both hit the same usage limit.
