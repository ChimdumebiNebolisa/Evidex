# Evidex Silver Adjudication v1

Blinded, progressive-disclosure silver adjudication over the Analysis v2
diagnostic cohort. This directory holds **four** judge-family artifacts.
They are not interchangeable.

| Artifact | Role | Location |
|---|---|---|
| Cursor/Grok five-judge A→B→C | **Primary mechanism study** | `cursor_panel/` |
| GLM-5.3 Stage A | **Supporting** replication vs Cursor Stage A | `judgments/stage_a/` + `cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md` |
| Claude residual Stage C | **Supporting** test on 231 Grok leftovers | `claude_residual_panel/` |
| Claude full A→B→C | **Main cross-family replication** on 226 regressions | `claude_full_regression_panel/` |

**What this is:** model-based silver labels that decompose why designated gold
evidence sometimes fails to produce the expected verdict (utilization vs
representation vs residual ambiguity).

**What this is not:** human ground truth, or proof that FEVER labels are wrong.
Within-family agreement overstates how much separate human raters would agree.

Study-level entry: repository [`README.md`](../README.md).
Limitations: [`docs/LIMITATIONS.md`](../docs/LIMITATIONS.md) and each panel's
`reports/LIMITATIONS.md`.

## Shared layout

- `prompts/` — judge rubric and disclosure protocol (do not edit after the fact)
- `data/blinded/` — shared blinded stage files
- `data/derived/` — cohort, ID map, GLM Stage A freeze
- `judgments/` — GLM outputs (Stage A complete; later stages provenance only)
- `src/` — Cursor/GLM pipeline, including `cross_panel_stage_a.py`
- `cursor_panel/`, `claude_residual_panel/`, `claude_full_regression_panel/`
- `blind_io/` — Claude-full judge-facing packets (neutral paths)

## Reproduce (no new judging)

```bash
python src/verify_headlines.py --panel cursor
python src/verify_glm_stage_a.py
python claude_residual_panel/src/verify_headlines.py
python claude_full_regression_panel/src/verify_headlines.py
```

`--panel cursor` is required for the Grok verifier. The default panel name is
GLM. GLM Stages B/C were never completed and are not part of A→B→C math.

Judge inference is finished. Frozen judgment files are the record.
