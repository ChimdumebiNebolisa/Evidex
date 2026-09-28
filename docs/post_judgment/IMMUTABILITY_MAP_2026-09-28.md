# Immutability map — 2026-09-28

**Historical path map.** The organized-layout branch preserves this freeze at commit `33121b7`; moved files are checked at their new locations by `tools/verify_layout.py`. See `LAYOUT_MIGRATION_2026-09-28.md`. The original path restrictions below apply to the pre-layout commit.

Path-level map of what may and may not change on `codex/methodology-correction-v2` after the
required Stage C judgments (base commit `606681b`). This document sits outside every hash
inventory (the `docs/post_judgment/` directory is matched by none of the globs below), so adding or
editing it changes no contract. It was written after the judgments; it does not alter any freeze.

## 1. Historical pinned files — never edit, move or re-save

Contract: `corrections_v2/baseline/historical_inputs.json` (774 files) plus the annotated tag
`evidex-artifact-v1` (commit `29102c39427fac01ff46c77c28365feb91f6397b`, tag object
`37748c3c5ba05c3feb7b55074bc4ddc702816269`). Checked by `provenance.verify_historical`; CRLF→LF
is the only accepted byte equivalence.

| Area | Pinned files | Notes |
|---|---:|---|
| repository root | 50 | all root data files (`*_balanced_*`, `shared_task_dev.jsonl`) and `README.md`, `REPRODUCING.md`, `MARKDOWN_CONSISTENCY_AUDIT.md`, `PUBLICATION_ARTIFACT_AUDIT.md`, `presentation_dossier_comprehensive.md`, `professor_update.md` |
| `silver_adjudication_v1/` | 621 | panels, judgments, blind I/O, prompts, tables, reports |
| `analysis_v2/` | 42 | data, figures, reports, tables, README (the `src/` code is **not** pinned) |
| `paper/` | 21 | the whole historical manuscript, PDF, tables, sections, claim map |
| `archive_old_pipeline/` | 21 | |
| `parallel_shards_balanced_10000_v1/` | 8 | |
| `poster-presentation-info/` | 6 | |
| `docs/` | 5 | `ADJUDICATION_PROTOCOL.md`, `DATA_PROVENANCE.md`, `LIMITATIONS.md`, `STUDY_OVERVIEW.md`, `historical/README.md` |

## 2. Correction implementation fingerprint — never edit; adding a matching file also breaks it

Contract: `corrections_v2/generated/code_hashes.json` (37 entries), compared with
`provenance.implementation_files()`. The comparison is set-equal, so a **new** file matching any
glob below fails verification just as an edit does.

- Globs: `corrections_v2/*.py`, `corrections_v2/*.md`, `corrections_v2/tests/*.py`,
  `corrections_v2/baseline/*`, `corrections_v2/inputs/*.json`, `corrections_v2/protocol/*.md`,
  `corrections_v2/protocol/*.template.json`, `corrections_v2/.gitattributes`,
  `corrections_v2/.gitignore`.
- Named files outside those globs: `fever_evidence.py`, `resolve_gold_evidence.py`,
  `silver_adjudication_v1/src/{reconstruct_evidence,join_analysis_v2,taxonomy_legacy_v1,taxonomy_v2}.py`,
  `silver_adjudication_v1/claude_full_regression_panel/src/analyze.py`.
- The fingerprinted documents are `corrections_v2/{README,RERUN,VERIFICATION,CURSOR_HANDOFF,MANUSCRIPT_CHANGES,FINDINGS,INVENTORY_RECONCILIATION}.md`
  and `corrections_v2/baseline/README.md`. They are pre-execution snapshots. Successors are listed in
  `SUPERSEDED_DOCUMENTS_2026-09-28.md`; the originals stay byte-identical.

## 3. Spec freeze — never edit, never replace, never add a second freeze for this protocol

Contract: `corrections_v2/protocol/analysis_spec_2026-09-27.freeze.json`
(`post_hoc_correction_v2_2026-09-27`, frozen `2026-09-27T06:35:44Z`, judgment outputs absent at
freeze). Checked by `analysis_io.verify_spec`; `analysis_io.spec_files` also globs
`corrections_v2/analysis_*.py`, so a new file with that name pattern breaks the freeze too.
The 18 pinned files are:

`corrections_v2/.gitattributes`, `CURSOR_HANDOFF.md`, `analysis_core.py`, `analysis_io.py`,
`analysis_pipeline.py`, `baseline/historical_inputs.json`, `baseline/page_snapshot.json`,
`generated/rerun_manifest.json`, `protocol/analysis_spec_2026-09-27.md`,
`protocol/execution.template.json`, `provenance.py`, `rerun.py` (all under `corrections_v2/`);
`silver_adjudication_v1/{claude_full_regression_panel,claude_residual_panel,cursor_panel}/config.json`,
`silver_adjudication_v1/prompts/{judge_rubric,resolver_rubric}.md`, `silver_adjudication_v1/src/taxonomy_v2.py`.

The retry cap (three attempts), session-uniqueness rule and first-schema-valid rule live in the
frozen `analysis_io.py` and are therefore unchangeable here.

## 4. Prepared-input inventory — never edit

Contract: `corrections_v2/generated/output_hashes.json` (103 entries; CRLF not tolerated):
`corrections_v2/generated/*.json|jsonl|csv` (18 files) and the 85 blind packets
`corrections_v2/blind_io/{p01:55,p02:15,p03:15}/**/*.json` excluding `*.output.json`.

## 5. Judgment evidence — append-only, byte-exact

- The 70 accepted outputs `corrections_v2/blind_io/{p01,p02}/stage_c/*.output.json`. Their hashes
  are recorded in `corrections_v2/execution/<job>/attempt-NN.json` and checked by the frozen
  validator.
- Execution records `corrections_v2/execution/<job>/attempt-NN.{json,raw.txt,routing.txt,hooks.jsonl,sdk-events.jsonl}`
  for every attempt, including failures. Byte-exact via `corrections_v2/execution/.gitattributes`
  (`* -text`).
- Post-judgment evidence `corrections_v2/deviation_review/evidence/**` (byte-exact via its own
  `.gitattributes`), including the recovered WSL outputs in `evidence/recovered_wsl_outputs/`.
- Committed provisional results `corrections_v2/deviation_review/provisional_results/**`
  (byte-exact). New results need a new dated name; `provisional_analysis.py run` refuses to
  overwrite.
- There is no `corrections_v2/results/` directory and no judgment freeze. Creating either would
  claim a frozen-protocol primary analysis that does not exist.

## 6. Safe to change or add

| Location | Status |
|---|---|
| `docs/post_judgment/**` | new dated documents (this directory) |
| `CURRENT_STATUS.md` (root) | new, unpinned entry point |
| `paper_corrected_draft/**` | new corrected manuscript draft; `paper/` stays pinned |
| `corrections_v2/deviation_review/*.md`, `provisional_analysis.py`, `tools/`, `tests/` | post-judgment code and docs; no glob matches this subdirectory |
| `corrections_v2/sdk_execution/**` | not pinned, but kept in place as the operational record of how outputs were produced |
| `scripts/**` | not pinned; the historical runners are named by pinned docs, so do not rename them |
| `analysis_v2/src/**`, `analysis_v2/tests/**`, unpinned `silver_adjudication_v1/**/*.py` | not pinned, but they are the historical pipelines behind pinned outputs; leave them in place |
| root `.gitignore`, `LICENSE`, `CITATION.cff`, `requirements-openai.txt` | unpinned; conventional root files |
| root `*.py` other than `fever_evidence.py` / `resolve_gold_evidence.py` | unpinned bytes, but named in pinned `REPRODUCING.md` / `PUBLICATION_ARTIFACT_AUDIT.md` and imported through `experiment_config.py`; do not move before submission (see `ROOT_MIGRATION_PLAN_2026-09-28.md`) |

Verifiers that enforce sections 1–5: `python corrections_v2/verify_outputs.py`,
`python corrections_v2/rerun.py validate --scope required`,
`python corrections_v2/analysis_pipeline.py status --panel primary`.
