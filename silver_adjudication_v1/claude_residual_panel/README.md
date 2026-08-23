# Claude residual Stage C panel

Cross-family validation of the Cursor/Grok Stage C residual
Ambiguous/Unresolved set.

- Model lock: `claude-opus-5-thinking-high` for all five judges
- Scope: residual items only (expected n = 231)
- Stage C evidence only; no new retrieval
- Primary result: raw five-judge consensus (resolver not run)
- This is **not** independent human validation

Judges never see Cursor/Grok/GLM/FEVER/GPT/NLI/cohort labels, and never
see that the items are a residual subset.

Batch 03 was resumed on a second Cursor account after the first account
exhausted Claude usage. The locked model and protocol did not change.

Start with `reports/CLAUDE_FINDINGS.md` and
`reports/FINAL_EVIDEX_STRENGTHENING.md`.
