# Study overview

This page walks the Evidex architecture. It does not replace the layer-specific findings reports.

Start at the [root README](../README.md) for headline numbers. Reproduce them with [REPRODUCING.md](../REPRODUCING.md).

## Architecture

```text
FEVER dev (Supported/Refuted)
        ↓
10,000-claim balanced sample  →  gold-evidence resolution
        ↓
GPT-5.4 and GPT-5.4-mini × {claim_only, claim_plus_evidence}
        ↓  40,000 predictions
Analysis v2 paired transitions
        ↓
1,061-claim diagnostic cohort (226 / 335 / 250 / 250)
        ├─ solid → Cursor/Grok A→B→C  →  Grok mechanism taxonomy
        ├─ dashed → GLM-5.3 Stage A replication
        ├─ dashed → Claude Stage C on 231 Grok leftovers
        └─ solid → Claude A→B→C on 226 regressions  →  Claude taxonomy
                            ↓
              Cross-family synthesis (ordering shared;
              proportions judge-family-sensitive)
```

The mermaid version of this map lives in the root README.

## What each layer answers

| Layer | Question | Canonical report |
|---|---|---|
| GPT 10K | Does gold evidence raise accuracy, and do some claims regress? | Root summaries; Analysis v2 FINDINGS |
| Analysis v2 | How are transitions structured? What correlates with regression? | `analysis_v2/reports/FINDINGS.md` |
| Cursor/Grok A→B→C | Under blinded progressive disclosure, which regression mechanisms appear? | `cursor_panel/reports/SILVER_FINDINGS.md` |
| GLM Stage A | Does another judge family agree at sentence-only evidence? | `CROSS_PANEL_STAGE_A_REPLICATION.md` |
| Claude residual | Of Grok's remaining Stage C leftovers, how many stay ambiguous under Claude? | `claude_residual_panel/reports/CLAUDE_FINDINGS.md` |
| Claude full A→B→C | Does an independent A→B→C panel on all 226 regressions reproduce the mixed-mechanism picture? | `claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` |

## What is not in the core path

- 1,000-claim balanced files and all `*_pilot` artifacts at the repo root
- `archive_old_pipeline/`
- Incomplete GLM Stages B and C (provenance only)
- Claude full `STOPPING_POINT.json` (interruption snapshot; the panel later finished)
- Historical memos listed in [`historical/README.md`](historical/README.md)

## Figures

Manuscript-facing cross-family figure: `silver_adjudication_v1/claude_full_regression_panel/figures/fig1_mechanism_by_family.png`.

Claude residual figures remain supporting. Do not use them as the final validation graphic.
