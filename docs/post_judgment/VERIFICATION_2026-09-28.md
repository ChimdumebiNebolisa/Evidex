# Verification record (2026-09-28)

All commands below ran on 2026-09-28 in a detached Git worktree of local commit
`e94d9e8` (branch `codex/methodology-correction-v2`, parent `606681b`), created
with `git worktree add --detach` in the temporary directory and removed
afterwards. Platform: Windows 10.0.26200, Python 3.12.10, `core.autocrlf=true`.
The historical tag `evidex-artifact-v1` resolved in the worktree to tag object
`37748c3c5ba05c3feb7b55074bc4ddc702816269` and commit
`29102c39427fac01ff46c77c28365feb91f6397b`.

No judge was launched and no model was called. After all commands, `git status
--porcelain` in the worktree listed nothing except ignored `__pycache__` and
`.pytest_cache` directories: no tracked file was modified and no untracked file
was written.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `python corrections_v2/verify_outputs.py` | 0 | PASS: 774 historical inputs (762 exact bytes, 12 EOL-only); output and code inventories valid; 1,061 exact selected sets; A/B retained; 85 prepared C jobs; 7,585 dependency links. Its fixed closing phrase "corrected judgments pending" is stale text in fingerprinted code and is not a finding. |
| `python corrections_v2/rerun.py validate --scope required` | 0 | 70/70 required jobs and 6,430/6,430 judgments schema-valid. Execution provenance reported as `not_assessed_no_execution_log_validator`; optional panel p03 incomplete (0/15 jobs, not run). |
| `python corrections_v2/analysis_pipeline.py status --panel primary` | 1 | Expected. `status: incomplete`; retry limit exceeded for p01_C_j4_b08, p01_C_j4_b09, p02_C_j2_b03, p02_C_j3_b01, p02_C_j3_b02, p02_C_j3_b03, plus `reused_session`. `scientific_estimates: not_computed`, `inference_launched: false`. |
| `python -m unittest discover -s corrections_v2/tests -v` | 0 | 37 tests passed (67.9 s). |
| `python -m unittest discover -s corrections_v2/deviation_review/tests -v` | 0 | 6 tests passed. |
| `python corrections_v2/deviation_review/provisional_analysis.py verify` | 0 | PASS: 8 alternative inputs validated against recorded hashes before analysis; all semantic checks true; Grok sensitivity separation holds (no regression-cohort field changes); no byte differences from the committed `provisional_results/` apart from `status.json:created_at_utc`. |
| `python paper_corrected_draft/check_draft.py` | 0 | PASS: 14 files, 29 labels, 11 references, 20 citations; withdrawn numbers appear only in the withdrawn-results appendix. |
| `python scripts/run_all_tests.py` | 0 | All four historical suites passed: `analysis_v2` 10 (pytest), `silver_adjudication_v1` 45 (1 skipped), `claude_residual_panel` 20 (1 skipped), `claude_full_regression_panel` 27. |
| `python scripts/verify_all_headlines.py` | 0 | All level-1 headline checks passed, including 38/38 and 21/21 panel headlines. |
| `git diff --check` (worktree) and `git diff --check 606681b HEAD` | 0, 0 | No whitespace errors. |

The historical runners needed no installation: pytest, pandas, NumPy, SciPy,
pyarrow, matplotlib and statsmodels were already present. A pass from
`verify_all_headlines.py` means the historical documents still match the
historical data. It does not mean those historical claims are valid; several of
them (for example Grok Stage C 38.1% and Claude 28.8%) are withdrawn in
`paper_corrected_draft/` and in the post-judgment analysis note.

## Not run, and why

| Command | Reason |
|---|---|
| `python corrections_v2/tests/check_clean_checkout.py --autocrlf true/false` | It runs `corrections_v2/reproduce.py` against the delivered outputs in a clone, which this task prohibits. It also still expects `rerun.py validate --scope required` to exit 1, which was true before Stage C outputs existed; it now exits 0, so the script would fail on stale expectations rather than on a defect. It is fingerprinted and was not edited. |
| `python corrections_v2/reproduce.py` | Prohibited against delivered outputs. |
| LaTeX build of `paper_corrected_draft/` | No toolchain is installed (pdflatex, latexmk, tectonic, bibtex and pandoc are absent on Windows and WSL). `check_draft.py` is a static substitute, not a compile. |

## Main-repository check

`git diff --check` in the main working tree also exited 0 before the verification
commit, and `git diff --cached --check` exited 0 before the commit that added this
record.
