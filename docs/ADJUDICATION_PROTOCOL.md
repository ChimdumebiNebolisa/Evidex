# Adjudication protocol (pointers)

The protocol is already written and versioned with the experiments. This page tells you where it lives. It does not replace the rubric.

## Shared protocol files

Do not edit these as part of documentation cleanup:

- [`silver_adjudication_v1/prompts/judge_rubric.md`](../silver_adjudication_v1/prompts/judge_rubric.md)
- [`silver_adjudication_v1/prompts/progressive_disclosure_protocol.md`](../silver_adjudication_v1/prompts/progressive_disclosure_protocol.md)
- [`silver_adjudication_v1/prompts/resolver_rubric.md`](../silver_adjudication_v1/prompts/resolver_rubric.md) (Cursor/Grok resolver only)

## Progressive disclosure

| Stage | What judges see |
|---|---|
| A | Sentence-level evidence only |
| B | Stage A plus page titles |
| C | Reconstructed structured FEVER evidence |

Stages are frozen before the next stage’s packets are built. Judges do not browse, retrieve new evidence, or see GPT/FEVER/NLI/other-panel labels.

## Isolation

Five isolated judges per panel. Fresh context per `(judge, batch, stage)`. One context must not simulate five judges.

## Model locks

| Panel | Locked model |
|---|---|
| Cursor/Grok | `cursor-grok-4.6-high-fast` |
| GLM Stage A | GLM-5.3 |
| Claude residual | `claude-opus-5-thinking-high` |
| Claude full regression | `claude-opus-5-thinking-high` |

If the locked model is unavailable, the protocol is to stop and record missing work. No substitution.

## Freeze before unblinding

Each completed panel writes freeze manifests and hashes blinded inputs and judgments. Consensus and taxonomy are defined in code; they are not hand labels. Verifiers recompute hashes from disk.

## Claude full-panel path hygiene

Judge-facing I/O for the 226-regression Claude panel lives under `silver_adjudication_v1/blind_io/` so packet paths do not name the cohort selection criterion.

## Methods write-ups

- Cursor/Grok: `cursor_panel/reports/SILVER_FINDINGS.md` and `LIMITATIONS.md`
- GLM vs Cursor Stage A: `cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md`
- Claude residual: `claude_residual_panel/reports/METHODS.md`
- Claude full: `claude_full_regression_panel/reports/METHODS.md`
