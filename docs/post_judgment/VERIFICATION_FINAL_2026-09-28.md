# Final verification — commit `0dcfa74` (2026-09-28)

Branch `codex/methodology-correction-v2`, four local commits ahead of
`origin/codex/methodology-correction-v2`; not pushed. Run on a clean worktree at `0dcfa74`
(Windows, Python 3; LaTeX under WSL, TeX Live 2025). No command launched inference.

| Command | Exit | Result |
|---|---|---|
| `python corrections_v2/verify_outputs.py` | 0 | PASS: 774 historical inputs (exact bytes), inventories valid |
| `python corrections_v2/rerun.py validate --scope required` | 0 | 70 jobs, 6,430 schema-valid; provenance not assessed by this command |
| `python corrections_v2/analysis_pipeline.py status --panel primary` | 1 | `incomplete` (expected): retry limit exceeded for six jobs, plus `reused_session` |
| `python corrections_v2/amendment_2026-09-28/amended_analysis.py status` | 0 | `ready_under_amendment_A1`: 102 records (88 own, 13 collision, 1 not launched), 101 launched slots, 101 distinct agents |
| `python corrections_v2/amendment_2026-09-28/amended_analysis.py verify` | 0 | PASS: 60 result files reproduce (timestamps ignored) |
| `python corrections_v2/deviation_review/provisional_analysis.py verify` | 0 | PASS |
| `python -m unittest discover -s corrections_v2/tests` | 0 | 37 tests OK |
| `python -m unittest discover -s corrections_v2/deviation_review/tests` | 0 | 6 tests OK |
| `python -m unittest discover -s corrections_v2/amendment_2026-09-28/tests` | 0 | 6 tests OK |
| `python scripts/run_all_tests.py` | 0 | all suites passed |
| `python scripts/verify_all_headlines.py` | 0 | 21/21 headlines; all level-1 checks |
| `python paper_corrected_draft/make_assets.py` | 0 | regenerated tables and figures identical to the committed files |
| `python paper_corrected_draft/check_draft.py` | 0 | PASS (14 files, 31 labels, 13 refs, 20 citations) |
| `latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex` (WSL, in `paper_corrected_draft/`) | 0 | 20 pages; 0 overfull boxes, 0 undefined references or citations; text identical to `evidex-corrected-draft.pdf` |
| `git diff --check @{u}..HEAD` | 0 | clean |

`git diff --stat @{u}..HEAD` is empty for `corrections_v2/execution`, `corrections_v2/blind_io`,
`corrections_v2/protocol`, the frozen analysis modules and taxonomy, `corrections_v2/baseline`,
`corrections_v2/generated`, `paper/` and `silver_adjudication_v1/`. Tag `evidex-artifact-v1`
still points to tag object `37748c3c…`, commit `29102c39…`.

`session_evidence.json` was produced once by `amended_analysis.py evaluate-sessions`, which reads
the 101 slot event logs from WSL. It checks each log against the SHA-256 recorded in
`deviation_review/evidence/wsl_inventory.json`. The WSL step is not part of routine verification;
`status`, `verify` and the tests use only tracked files.

## Addendum: manuscript-only follow-up commit

The next commit removes operational execution detail from the manuscript. It drops usage and
quota limits, provider errors, runner and session mechanics, and attempt-record counts; that
detail remains in corrections_v2/amendment_2026-09-28/ and corrections_v2/deviation_review/.
It changes only paper_corrected_draft/ sources and the PDF, CURRENT_STATUS.md and this file.
Re-run for that commit: check_draft.py PASS; latexmk exit 0, 19 pages, 0 overfull boxes,
0 undefined references or citations; git diff --check clean. No result, table or figure changed.
