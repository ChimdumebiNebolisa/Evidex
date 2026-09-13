# Claude residual Stage C panel

Supporting Stage C robustness test on the 231 Cursor/Grok residual
Ambiguous/Unresolved items. This is **not** the main Claude replication.

The later full A→B→C replication on all 226 regressions is
[`../claude_full_regression_panel/`](../claude_full_regression_panel/)
(3,390 judgments). Study-level final synthesis:
[`../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`](../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md).

- Model lock: `claude-opus-5-thinking-high` for all five judges
- Scope: residual items only (expected n = 231)
- Stage C evidence only; no new retrieval
- Primary result: raw five-judge consensus (resolver not run)
- This is **not** independent human validation

Judges never see Cursor/Grok/GLM/FEVER/GPT/NLI/cohort labels, and never
see that the items are a residual subset.

Batch 03 was resumed on a second Cursor account after the first account
exhausted Claude usage. The locked model and protocol did not change.

Start with [`reports/CLAUDE_FINDINGS.md`](reports/CLAUDE_FINDINGS.md)
(primary report for this residual experiment).
[`reports/FINAL_EVIDEX_STRENGTHENING.md`](reports/FINAL_EVIDEX_STRENGTHENING.md)
is an intermediate historical synthesis.
