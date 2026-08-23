# Claude residual panel — incomplete (model lock)

Stopped 2026-08-23. `claude-opus-5-thinking-high` became unavailable
(Cursor "Other Models usage limit reached"; the runner offered
`grok-4.6`). Per protocol, **no substitution**.

## Progress

- Residual cohort independently reconstructed: **231** (212 Ambiguous +
  19 Unresolved from frozen Cursor Stage C consensus).
- Blinded file leakage check: **PASS**.
- Batches 01–02 complete for all five judges: **154 items × 5 = 770**
  valid raw judgments. Zero schema retries.
- Batch 03 remaining: **77 items × 5 = 385** judgments.
- Target if complete: 1,155.

## Not done (do not treat this as the final experiment)

- Batch 03 judging
- freeze / consensus / agreement
- cross-family comparison
- FEVER unblinding
- headline verification of a finished panel
- final mechanism assessment

Resume only with `claude-opus-5-thinking-high`. Packets for batch 03
already exist under `cache/packets/claude_judge_*_batch_03.json`.
Do not rerun valid batch 01–02 files.
