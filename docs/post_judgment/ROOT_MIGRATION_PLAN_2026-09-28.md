# Root clean-up: post-submission migration plan — 2026-09-28

**Decision: the repository root is not reorganized now.** Every candidate move conflicts with at
least one contract:

- the 774-file historical inventory, which pins 50 of the 66 root files by path;
- the correction code fingerprint, which names `fever_evidence.py` and `resolve_gold_evidence.py`
  at the root, and whose path list lives in the freeze-pinned `corrections_v2/provenance.py`;
- the reproduction commands in pinned documents (`REPRODUCING.md`, `PUBLICATION_ARTIFACT_AUDIT.md`,
  `professor_update.md`), which run root scripts by root path;
- root-relative data paths in fingerprinted code (`corrections_v2/reproduce.py`,
  `corrections_v2/build_report_data.py`) and in `analysis_v2/config.py` and
  `silver_adjudication_v1/config.py`.

Moving any of these files now would either break `verify_outputs.py` or silently invalidate a
documented command. This plan is for after submission, once the correction record is closed.

## Current root: 67 tracked files

The root had 66 files at `606681b`. `CURRENT_STATUS.md` is the only addition.

| Group | Files | Contract |
|---|---:|---|
| Source and sampling data (`fever_balanced_*_source.csv`, `sample_provenance_*`, `sample_validation_*`, `dataset_validation_*`, `resolve_summary_*`, `shared_task_dev.jsonl`) | 11 | historical inventory; read by `reproduce.py`, `build_report_data.py` |
| Experiment data (`experiment_runs_*`, `experiment_results_*`, `experiment_tracker*_*`) | 12 | historical inventory; read by `reproduce.py`, `analysis_v2/config.py`, `merge_parallel_results.py` |
| Behavioral summaries (`experiment_metrics_*`, `experiment_summary_*`, `error_taxonomy_counts_*`, `evidence_condition_errors_*`, `example_failure_cases_*`, `manual_annotations_*`) | 21 | historical inventory |
| Historical documents (`README.md`, `REPRODUCING.md`, `MARKDOWN_CONSISTENCY_AUDIT.md`, `PUBLICATION_ARTIFACT_AUDIT.md`, `presentation_dossier_comprehensive.md`, `professor_update.md`) | 6 | historical inventory |
| Correction-pinned code (`fever_evidence.py`, `resolve_gold_evidence.py`) | 2 | code fingerprint; imported by `corrections_v2/reproduce.py`, `corrections_v2/tests/test_corrections.py`, `silver_adjudication_v1/src/reconstruct_evidence.py` |
| Pipeline scripts (`aggregate_manual_annotations`, `analyze_experiment_results`, `create_pilot_runs_subset`, `expand_experiment_runs`, `experiment_config`, `extract_fever_balanced_sample`, `merge_parallel_results`, `parallelize_remaining_runs`, `prepare_fever_wiki_pages`, `run_fact_check_experiment`) | 10 | bytes unpinned; invoked by root path in pinned docs; `experiment_config` is imported by `resolve_gold_evidence.py` and seven other root scripts |
| Conventional root files (`.gitignore`, `LICENSE`, `CITATION.cff`, `requirements-openai.txt`) | 4 | none; stay at root |
| Entry point (`CURRENT_STATUS.md`) | 1 | none |

## Proposed mapping (after submission)

| From (root) | To |
|---|---|
| source and sampling data (11) | `data/source/` |
| experiment data (12) | `data/experiment/` |
| behavioral summaries (21) | `results/behavioral/` |
| `*_1000_v1*` and `*_pilot*` variants, within the groups above | `data/pilot/` or `results/pilot/`, keeping file names |
| `MARKDOWN_CONSISTENCY_AUDIT.md`, `PUBLICATION_ARTIFACT_AUDIT.md`, `presentation_dossier_comprehensive.md`, `professor_update.md` | `docs/historical/` |
| 10 pipeline scripts plus `fever_evidence.py`, `resolve_gold_evidence.py` | `pipeline/` (a package; `experiment_config` imported as `pipeline.experiment_config`) |
| `README.md`, `REPRODUCING.md` | stay at root as new versions; the pinned versions move to `docs/historical/` |

## Verifier and code changes the move requires

1. **Historical inventory.** Keep `corrections_v2/baseline/historical_inputs.json` unchanged. Add a
   successor verifier in a new, dated location (not `corrections_v2/`) that reads a rename map
   `{old_path: new_path}`. For each entry it compares the bytes at
   `git show evidex-artifact-v1:<old_path>` with `HEAD:<new_path>` under the same CRLF→LF rule, and
   it rejects any path that is unmapped or duplicated. The frozen `provenance.verify_historical` will
   then fail by design. The successor must say so rather than patch it.
2. **Correction fingerprint and freeze.** Moving `fever_evidence.py` or `resolve_gold_evidence.py`,
   or editing the `sys.path`/data-path lines in `reproduce.py`, `build_report_data.py` and
   `tests/test_corrections.py`, changes files named in `code_hashes.json` and in the freeze-pinned
   `provenance.py`. Do this only as a new, separately named correction version. Leave
   `correction_v2` and its freeze as the historical record, verifiable at the pre-migration commit.
3. **Root-relative data paths.** Update `analysis_v2/config.py` (`SOURCE_RESULTS`),
   `silver_adjudication_v1/config.py`, `merge_parallel_results.py` and
   `extract_fever_balanced_sample.py` to the new data paths. These files are unpinned. Re-run
   `scripts/verify_all_headlines.py` and `scripts/run_all_tests.py` afterwards.
4. **Imports.** Replace `from experiment_config import …` in the eight importers, and root imports
   of `fever_evidence` / `resolve_gold_evidence`, with package imports.
5. **Documented commands.** Write a new `REPRODUCING.md` with the new commands. Keep the pinned one
   as a dated historical copy and cite the migration commit from `CURRENT_STATUS.md`.
6. **Tag.** Create a new annotated tag for the migrated layout. Never move `evidex-artifact-v1`.

## Acceptance checks for the migration commit

- The successor rename verifier passes for all 774 historical paths.
- `scripts/verify_all_headlines.py` and `scripts/run_all_tests.py` pass.
- The new correction version's own verifier passes.
- At the pre-migration commit, `python corrections_v2/verify_outputs.py` still passes, so the old
  record stays checkable.
- `git grep` finds no reference to an old root path outside `docs/historical/` and the rename map.
