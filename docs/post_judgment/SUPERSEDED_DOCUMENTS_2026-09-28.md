# Superseded documents — successor index, 2026-09-28

The documents below are dated snapshots. Each one is hash-pinned, either by the 774-file historical
inventory or by the correction code fingerprint, so it cannot be edited or annotated in place without
breaking verification. This index is their successor. The current entry point is `CURRENT_STATUS.md`
in the repository root.

| Document | Pinned by | Snapshot of | What is out of date | Successor |
|---|---|---|---|---|
| `README.md` (root) | historical inventory | study at tag `evidex-artifact-v1` | presents the v1 mechanism splits (50.0/11.9/38.1, 65.9/5.3/28.8), the ordering claim and κ=0.537 as findings | `CURRENT_STATUS.md`; `paper_corrected_draft/CLAIM_MAPPING.md` |
| `REPRODUCING.md` (root) | historical inventory | reproduction of the v1 artifact | still correct for the behavioral and v1 records. It does not cover correction v2 or the post-judgment analysis | `CURRENT_STATUS.md` (commands table) |
| `professor_update.md`, `presentation_dossier_comprehensive.md`, `MARKDOWN_CONSISTENCY_AUDIT.md`, `PUBLICATION_ARTIFACT_AUDIT.md` (root) | historical inventory | pre-correction reporting and audits | diagnostic statements rest on the defective v1 Stage C | `docs/post_judgment/POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md` |
| `paper/**` | historical inventory | historical manuscript draft and PDF | withdrawn diagnostic claims, figures and tables | `paper_corrected_draft/` |
| `docs/STUDY_OVERVIEW.md`, `docs/LIMITATIONS.md`, `docs/ADJUDICATION_PROTOCOL.md`, `docs/DATA_PROVENANCE.md` | historical inventory | v1 study documentation | v1 taxonomy and Stage C description | the note above; `paper_corrected_draft/sections/study_design.tex` |
| `silver_adjudication_v1/README.md`, `analysis_v2/README.md` | historical inventory | v1 pipelines | v1 diagnostic interpretation (the `analysis_v2` behavioral content stays current) | the note above |
| `corrections_v2/README.md` | code fingerprint | pre-execution correction package | "corrected-packet judgments pending" | `CURRENT_STATUS.md` |
| `corrections_v2/RERUN.md` | code fingerprint | pre-execution rerun instructions | "every completion command exits 1 because no judgments have been executed" | `CURRENT_STATUS.md`; `corrections_v2/deviation_review/attempt_table.md` |
| `corrections_v2/VERIFICATION.md` | code fingerprint | pre-execution verification log | expected-exit table and "pending" status | `CURRENT_STATUS.md` (commands table); `docs/post_judgment/VERIFICATION_2026-09-28.md` |
| `corrections_v2/CURSOR_HANDOFF.md` | code fingerprint **and** spec freeze | execution handoff | describes judging as future work | `corrections_v2/deviation_review/DEVIATION_ASSESSMENT_2026-09-28.md` |
| `corrections_v2/FINDINGS.md` | code fingerprint | audit findings before new judgments | corrected-packet rows marked PENDING | `docs/post_judgment/POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md` |
| `corrections_v2/MANUSCRIPT_CHANGES.md` | code fingerprint | proposed manuscript changes pending reruns | "corrected … await fresh Stage C judgments" | `paper_corrected_draft/CLAIM_MAPPING.md` |
| `corrections_v2/INVENTORY_RECONCILIATION.md` | code fingerprint | pre-execution inventory | predates execution records and deviation evidence | `docs/post_judgment/IMMUTABILITY_MAP_2026-09-28.md` |
| `corrections_v2/sdk_execution/PROPOSED_FIRST_JOBS.md`, `SETUP_VALIDATION_2026-09-27.md`, `WSL2_ISOLATION_CHECK_2026-09-27.md` | not pinned (dated execution setup records) | setup before execution | proposals and checks before the runs. Kept unedited as the operational record | `corrections_v2/deviation_review/attempt_table.md` |

Two stale messages come from fingerprinted code, so they cannot be changed:

- `python corrections_v2/verify_outputs.py` ends with the fixed phrase "corrected judgments pending".
- `rerun.py validate` reports execution provenance as "not_assessed".

The authoritative provenance status is `python corrections_v2/analysis_pipeline.py status --panel primary`,
which reports `incomplete`.
