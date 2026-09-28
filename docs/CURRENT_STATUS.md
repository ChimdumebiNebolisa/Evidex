# Evidex current status — 2026-09-28

The current manuscript is [`paper_corrected_draft/evidex-corrected-draft.pdf`](../paper_corrected_draft/evidex-corrected-draft.pdf), a coauthor-review draft. Venue formatting and affiliations are still placeholders.

| Study layer | Status |
|---|---|
| Behavioral predictions | 40,000 original predictions across 10,000 FEVER claims. The +7.35 and +10.87 percentage-point gains and 226 distinct regressions are unchanged. |
| Historical diagnostic Stage C | Defective sentence extraction and a taxonomy that conflated disagreement with FEVER and evidence use. Old mechanism shares are withdrawn. |
| Corrected Stage C | 70 required jobs and 6,430 schema-valid judgments completed, with repaired evidence. A/B judgments are retained from the earlier panel. |
| Original frozen correction protocol | Primary execution status remains incomplete under its original attempt and output-selection rules. The frozen protocol and tag are unchanged. |
| Dated amendment A1 | Accepted outputs are analysed under an explicitly post-judgment amendment; first-valid outputs are a sensitivity check. Its results are in `corrections_v2/amendment_2026-09-28/results/`. |
| Optional follow-ups | New residual Claude panel, Stage C resolver and human adjudication were not run. |

This branch reorganizes old files into `historical/` and moves old root reports into `docs/historical/`. The [layout migration note](post_judgment/LAYOUT_MIGRATION_2026-09-28.md) and [reproduction guide](../REPRODUCING.md) explain the path map and verification commands. Historical documents that still describe withdrawn results remain clearly separated from the current draft; read them as archival records.
