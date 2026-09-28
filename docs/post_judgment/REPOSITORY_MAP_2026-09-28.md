# Repository map (2026-09-28)

**Historical pre-layout inventory.** The current map is in the root `README.md`, and the 121 moves are recorded in `LAYOUT_MIGRATION_2026-09-28.md`. Counts and links below describe the pre-layout commit.

This is a map of the repository as of branch `codex/methodology-correction-v2`.
Start at [`CURRENT_STATUS.md`](../../CURRENT_STATUS.md). The machine-readable
file inventory, with a movability verdict for every Python file and root file,
is [`repository_inventory_2026-09-28.json`](repository_inventory_2026-09-28.json)
(regenerate with `python scripts/repository_inventory.py --json OUT`). That
snapshot was taken before this map, the verification note and the JSON file
itself were added, so it counts 1,779 tracked files rather than 1,782; no
verdict changes, because all three are documentation.

Nothing listed as pinned, fingerprinted, frozen or append-only below may be
moved or edited; see [`IMMUTABILITY_MAP_2026-09-28.md`](IMMUTABILITY_MAP_2026-09-28.md).
Why the root is not reorganized is explained in
[`ROOT_MIGRATION_PLAN_2026-09-28.md`](ROOT_MIGRATION_PLAN_2026-09-28.md).

## Top-level areas

| Path | Tracked files | Role | Status |
|---|---:|---|---|
| repository root | 67 | Original behavioral pipeline scripts, FEVER source samples, experiment runs and summaries, original README/REPRODUCING/audit docs, `CURRENT_STATUS.md` | 50 files pinned by the historical inventory; `fever_evidence.py` and `resolve_gold_evidence.py` fingerprinted |
| `analysis_v2/` | 66 | Historical v2 behavioral analysis (transition matrices, NLI disagreement, figures) | 42 files pinned; the rest historical, left in place |
| `silver_adjudication_v1/` | 720 | Historical silver-label adjudication pipeline, including `src/taxonomy_v2.py` used by the correction analysis | 621 files pinned; five `src/` files fingerprinted |
| `archive_old_pipeline/` | 21 | Superseded early pipeline | Pinned |
| `parallel_shards_balanced_10000_v1/` | 8 | Shards of the 10,000-claim behavioral run | Pinned |
| `paper/` | 23 | Original submitted manuscript | 21 files pinned; superseded by `paper_corrected_draft/` for content |
| `poster-presentation-info/` | 6 | Original poster material | Pinned |
| `docs/` | 13 | Original study docs (pinned) plus `docs/post_judgment/` (this map and the other dated notes) | Original five pinned |
| `scripts/` | 3 | `run_all_tests.py`, `verify_all_headlines.py` (historical runners) and `repository_inventory.py` (read-only inventory) | Runners named by pinned docs |
| `corrections_v2/` | 839 | The 2026-09-27 methodology correction: frozen protocol, frozen analysis code, blind inputs, judge execution records, accepted outputs, and the post-judgment deviation review | See below |
| `paper_corrected_draft/` | 16 | Corrected manuscript draft (not compiled), claim mapping, static checker | New; for coauthor review |

## `corrections_v2/`

| Path | Role | Status |
|---|---|---|
| `*.py` (top level) | Frozen correction code: `analysis_core.py`, `analysis_io.py`, `analysis_pipeline.py` (spec-frozen), `rerun.py`, `provenance.py`, `verify_outputs.py`, `reproduce.py`, `audit_freezes.py`, `build_report_data.py` | Fingerprinted; analysis files also spec-frozen |
| `*.md` (top level) | README, RERUN, VERIFICATION, FINDINGS, MANUSCRIPT_CHANGES, CURSOR_HANDOFF, INVENTORY_RECONCILIATION | Fingerprinted snapshots; successors listed in [`SUPERSEDED_DOCUMENTS_2026-09-28.md`](SUPERSEDED_DOCUMENTS_2026-09-28.md) |
| `protocol/` | Analysis spec, its freeze, execution template, two operational amendments | Frozen / fingerprinted |
| `baseline/`, `inputs/` | Historical inventory and prepared inputs | Fingerprinted |
| `generated/` | Code and output hash inventories, generated correction data | Output-hashed |
| `blind_io/` | 85 blind packets and the accepted judge outputs | Output-hashed / accepted outputs |
| `execution/` | Per-job attempt records and raw outputs (byte-exact via `* -text`) | Append-only evidence |
| `handoff_jobs/`, `handoff/` | Job files and the handoff archive given to the execution agent | Evidence |
| `sdk_execution/` | Execution tooling used to run the judges | Left in place (execution provenance) |
| `tests/` | Correction test suite | Fingerprinted |
| `draft_archive/` | Pointer to archived draft material | Unchanged |
| `deviation_review/` | Post-judgment deviation review (not part of the frozen protocol) | See below |

## `corrections_v2/deviation_review/`

| Path | Role |
|---|---|
| `DEVIATION_ASSESSMENT_2026-09-28.md` | Defensibility assessment for a dated deviation analysis |
| `attempt_table.md` | Chronological attempt table for the six jobs flagged by the frozen validator |
| `evidence/` | Attempt evidence JSON, WSL inventory, unstaged-output check, and `recovered_wsl_outputs/` (three byte-exact recovered files plus manifest) |
| `provisional_analysis.py` | Portable provisional analysis; `verify` reproduces `provisional_results/` byte-for-byte in a temporary directory |
| `provisional_results/` | Committed provisional (non-primary) results, tag `2026-09-28` |
| `tests/` | Input-portability and integrity tests for the provisional analysis |
| `tools/` | One-time evidence builders: `wsl_inventory.py`, `build_attempt_evidence.py` (needs local staging paths via environment variables), `check_unstaged_outputs.py`, `render_attempt_table.py`, `recover_wsl_outputs.py` |

## Entry points

| Question | Where to look |
|---|---|
| What is the current state? | `CURRENT_STATUS.md` |
| What may not be touched? | `docs/post_judgment/IMMUTABILITY_MAP_2026-09-28.md` |
| What do the correction results say, and with what caveats? | `docs/post_judgment/POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md` |
| How were inputs recovered and verified? | `docs/post_judgment/TECHNICAL_SUPPLEMENT_2026-09-28.md` |
| Which old documents are stale? | `docs/post_judgment/SUPERSEDED_DOCUMENTS_2026-09-28.md` |
| What was verified, with which exit codes? | `docs/post_judgment/VERIFICATION_2026-09-28.md` |
| What does the corrected paper claim? | `paper_corrected_draft/` and its `CLAIM_MAPPING.md` |
