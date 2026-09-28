# Evidex manuscript draft v1

Working title: *Evidence Helps on Average, but Sometimes Hurts: Diagnosing Evidence-Induced Regressions in LLM Fact Verification*

This directory is manuscript-only. It is branched from the immutable research tag `evidex-artifact-v1` (`29102c3`). Do not modify frozen experiment outputs from here.

## Compile

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
# or, if latexmk is unavailable:
# tectonic --keep-logs --keep-intermediates main.tex
```

The review PDF is written to `evidex-manuscript-draft.pdf` (copied from `main.pdf` after a successful build).

## Source hierarchy

Scientific numbers come from frozen tables, `HEADLINES.json`, `analysis_v2/tables/verification.md`, and `silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`. See `CLAIM_SOURCE_MAP.md`.

## Figures

Main-text figures are included from the frozen repository paths (not regenerated):

- `../analysis_v2/figures/fig1_transition_matrices.png`
- `../analysis_v2/figures/fig6_nli_disagreement.png`
- `../silver_adjudication_v1/claude_full_regression_panel/figures/fig1_mechanism_by_family.png`
- `../silver_adjudication_v1/claude_full_regression_panel/figures/fig2_stage_ambiguity.png`

Appendix figures use additional frozen PNGs under `cursor_panel/figures/` and `claude_full_regression_panel/figures/`.

## Review status

First complete draft for Dr. Jessica Udry. Venue-neutral. Not compressed for TACL/TMLR/JAIR page limits.
