# Verification record

Verified on 2026-09-27. No inference, push, merge or publication occurred.
Infrastructure checks do **not** validate corrected scientific conclusions.
Fresh corrected-packet judgments, execution provenance and downstream consensus
remain pending.

## Commands and observed exits

Run from the repository root. Below, `python` is Python 3.12.10 on Windows, or
`/home/evidex-validation-venv/bin/python` on Linux.

| Exact command | Windows exit/result | Linux exit/result |
|---|---|---|
| `python corrections_v2/reproduce.py` | 0, twice | 0, twice |
| `python corrections_v2/verify_outputs.py` | 0 after each run | 0 after each run |
| `python -m unittest discover -s corrections_v2/tests -v` | 0, 23 passed | 0, 23 passed |
| `python corrections_v2/rerun.py validate --scope required` | 1, expected: 70 jobs absent | 1, expected: 70 jobs absent |
| `python corrections_v2/rerun.py validate --scope all` | 1, expected: 85 jobs absent | 1, expected: 85 jobs absent |
| `python scripts/verify_all_headlines.py` | 0, all Level-1 checks passed | 1, residual raw-freeze checks only; numerical checks passed |
| `python scripts/run_all_tests.py` | 0, 100 passed / 2 skipped | 1, 97 passed / 2 skipped / 2 failures / 1 error, all three failures/errors in raw-freeze checks |
| `python corrections_v2/reproduce.py` after an isolated substantive historical edit | 1 before output writes | 1 before output writes |

`validate --scope optional` likewise exits 1 while its 15 jobs are absent.
Required schema-completeness exits 0 with all 70 valid required jobs, even if
optional jobs are absent or malformed; temporary fixtures verify this. `all`
needs all 85 valid jobs. These exits do not assert provider execution or valid
scientific consensus. Read-only preparation verification is independent of
future judgment completeness.

Reproduction includes report generation and the freeze/EOL audit, then hashes
finalized outputs. Separate downstream write commands are unnecessary. The
explicit equivalent snapshot argument is
`--pages corrections_v2/inputs/historical_pages.json`.

## Clean, tracked-checkout evidence

The integration test creates a temporary index, an unreferenced local candidate
commit, and a clean detached clone containing **127 tracked correction files**,
including generated inventories. It leaves the user's branch and index alone.
It reproduces twice, verifies after each run, compares complete output inventory
bytes between runs, runs the checks above, and proves a one-character historical
source edit fails without changing generated outputs. Synthetic judge files
exist only in temporary unit-test directories.

Actual top-level commands executed:

```powershell
python corrections_v2/tests/check_clean_checkout.py --autocrlf true
wsl -d Ubuntu -- sh -c 'TMPDIR=/home/evidex-validation-runs /home/evidex-validation-venv/bin/python /mnt/c/Users/Chimdumebi/evidex/corrections_v2/tests/check_clean_checkout.py --autocrlf false'
```

Both exited 0 for the integration assertions. Historical runner exits are
recorded separately, not converted into claims that those runners passed.

| Actual environment | Candidate commit | Repeat evidence |
|---|---|---|
| Native Windows 11 build 26200, Python 3.12.10, `core.autocrlf=true` | `03cdc1da3436caacc7c3a6758b6c84750e9147c3` | Both reproductions/verifications passed; output inventories byte-identical |
| Native Linux Python 3.14.4 in Ubuntu/WSL2, kernel 6.6.87.2, glibc 2.43, `core.autocrlf=false` | `45c55124661d316af7a46eef97792648c30c4656` | Both reproductions/verifications passed; output inventories byte-identical |

This is actual Windows and Linux execution, not Windows-only newline
simulation; Linux was WSL2, not a separate bare-metal host. Temporary schema
outputs and source-corruption tests are simulations, not judgment runs.

Retained local command logs and machine-readable `result.json`:

- Windows: `C:\Users\Chimdumebi\AppData\Local\Temp\evidex-clean-checkout-a9aityrh`.
- Linux: `/home/evidex-validation-runs/evidex-clean-checkout-_ylb7eg2`.

Earlier attempts exposed a missing clone-local `main` reference needed by a
preserved legacy test, and missing scikit-learn in the isolated Linux environment.
The fixture now creates that clone-only reference, the dependency was installed,
and the final runs above include these corrections. No legacy test or historical
artifact was edited to achieve these results. This record was updated after the
candidate runs; their commits identify the tested code, not a published release
or this final documentation revision.

## Historical preservation and byte integrity

| Checkout | Exact recorded raw bytes | Verified EOL-only equivalence | Substantive drift |
|---|---:|---:|---:|
| Existing Windows working tree | 774 | 0 | 0 |
| Clean Windows / CRLF historical checkout | 762 | 12 | 0 |
| Clean Linux / LF historical checkout | 225 | 549 | 0 |

The inventory now has 774 historical files, not 775: the correction-owned page
snapshot is pinned separately in `baseline/page_snapshot.json` and stored in
`inputs/historical_pages.json`. Its original acquisition hash is preserved.
Reviewed historical raw hashes remain fixed, alongside identities from source
commit `776d09b40e9161800bf87238eb2cac4fe102df8e`. Reproduction never refreshes
this baseline from current working bytes.

Only CRLF-to-LF substitution is allowed for historical text equivalence. Lone
CR, whitespace changes, altered values, missing/reordered records, Unicode/BOM
changes and final-newline changes are not normalized away. Binary artifacts
require exact bytes. Tests demonstrate exact/EOL distinction and rejection of
non-EOL drift. New correction packets require their **exact** UTF-8/LF bytes.
All 85 Windows/Linux packet byte strings and recorded SHA-256 identities were
directly compared and matched. Environment-specific integrity reports and
implementation revision fields can differ across checkouts; they truthfully
record those observations rather than hiding raw-byte differences.

On Linux, numerical checks passed: 69/69 Analysis v2, 33/33 Grok, 38/38 Claude
residual and 21/21 Claude full, plus the read-only GLM A check. The unchanged
residual verifier reports 13 raw-freeze mismatches; the correction audit accounts
for all 14 residual entries (13 EOL-only text entries and one exact binary entry).
Legacy tests have two residual freeze failures and one full-panel pre-unblinding
manifest error caused by LF-versus-CRLF hashes. The pinned whole-repository
inventory establishes no substantive drift in those historical files. These
raw-byte failures remain visible; no historical manifest was regenerated.

Nine scientific data artifacts were compared against reviewed HEAD after only
CRLF-to-LF folding and were unchanged: `behavioral_counts.json`,
`evidence_summary.json`, `taxonomy_summary.json`, `representative_cases.json`,
`evidence_audit.jsonl`, `sentence_validation.jsonl`, `stage_b_corrected.jsonl`,
`stage_c_corrected.jsonl`, and `taxonomy_rule_only.csv`. This preserves +7.35 and
+10.87 pp gains; 226 regressions/40 shared; 936/1,061 chosen-text mismatches,
including 190 regressions; and historical FEVER disagreement of 36/113 Grok and
46/149 Claude utilization cases. Rule-only reanalysis remains historical-input
analysis, not corrected-packet evidence.

`git diff --name-only -- . ':!corrections_v2'` returned no paths. The scientific
tag remains object `37748c3c5ba05c3feb7b55074bc4ddc702816269`, resolving to commit
`29102c39427fac01ff46c77c28365feb91f6397b`. Branch HEAD remains
`0cc36f04ce8bbfd2a62848760c71550242be78c4`; only temporary unreferenced test
commits were created. No historical artifact, freeze, manuscript or tag changed.

## Remaining gates

The 23 correction tests cover the original 13 evidence/taxonomy cases and 10 new
provenance, serialization and completion cases. Existing test skips concern
unavailable later-stage GLM judgments and an already-passed pre-manifest
lifecycle state; neither hides a correction test failure.

Before judgment execution, verify access to the exact locked model slugs and
fresh isolated execution route, and arrange complete routing/session/retry
provenance. The validator explicitly does not certify that provenance. Retaining
A/B rests on identical visible inputs and documented stage isolation, not
independently verified provider transcripts. Proposed taxonomy still requires
review. Fresh primary C judgments total 6,430; optional historical residual
judgments total 1,155. Resolver work and a newly selected residual cohort after
corrected Grok C are additional work with result-dependent counts. Fresh
consensus and v2 downstream analysis remain necessary before scientific claims.

## Offline-analysis extension verification — 2026-09-27

The preceding clean-checkout record documents the reproduction repair. The new
offline pipeline was subsequently implemented and tested with isolated synthetic
fixtures; the following is the current verification record for that extension.
No fixture judgments or estimates were written into live scientific directories.

| Exact command | Observed result |
|---|---|
| `python -m unittest discover -s corrections_v2/tests -v` | Exit 0; 37 tests passed on native Windows/Python 3.12.10; final run 98.552 s |
| `wsl -d Ubuntu -- sh -c 'TMPDIR=/home/evidex-validation-runs /home/evidex-validation-venv/bin/python -m unittest discover -s corrections_v2/tests -v'` | Exit 0; 37 tests passed on native Linux/WSL2 Python 3.14.4; 36.997 s |
| `python scripts/run_all_tests.py` | Exit 0; existing Windows tests: 100 passed, 2 skipped |
| `python scripts/verify_all_headlines.py` | Exit 0; all existing Windows headline checks passed |
| `python corrections_v2/reproduce.py` | Exit 0; historical 774 exact-byte matches, snapshot checked separately |
| `python corrections_v2/analysis_pipeline.py freeze-spec` | Exit 0; append-only post hoc protocol frozen at `2026-09-27T06:35:44.865222+00:00` with no judgment outputs present |
| `python corrections_v2/analysis_pipeline.py export-handoff` | Exit 0; 70 required + 15 optional one-packet archives, operator-only protocol/manifest/template |
| `python corrections_v2/analysis_pipeline.py status --panel primary` | Expected exit 1; 70 missing jobs, no scientific estimates |
| `python corrections_v2/analysis_pipeline.py freeze --panel primary` | Expected exit 1; no incomplete judgment freeze written |
| `python corrections_v2/analysis_pipeline.py analyze --panel primary --version run001` | Expected exit 1; pending, no result directory/table/plot/estimate written |
| `git diff --check` | Exit 0 |

The Linux extension test ran the actual Python/Linux process against the mounted
working-tree source, with temporary fixture data on Linux. It is not claimed to
be an additional fresh LF Git checkout test of this extension; the earlier
clean-checkout tests are separately identified above. Matplotlib was installed
into the isolated Linux validation environment to exercise real SVG generation.

The 14 new tests supplement the previous 23. Coverage includes all 243 five-judge
verdict patterns at weak-sufficiency counts 0/3/5 compared directly with the
historical function, explicit order-sensitive ties, missing/duplicate slots,
degenerate statistics/BH, exact inventory reconciliation, complete synthetic
primary/residual/resolver/optional analysis, A/B frozen-label equivalence,
versioned CSV/JSON/SVG outputs, new residual selection/blinding, incomplete gates,
provenance absence, wrong routing, reused sessions across panels, rejection of
discarded schema-valid attempts, protocol drift and immutable output freezes.
All generated scientific-looking fixture outputs were removed with their temp
directories. A first integration test found a result-path/DataFrame name collision;
the collision was fixed and the full test suites rerun successfully.

The live handoff archive is `handoff/cursor_handoff_2026-09-27.zip`, SHA-256
`4c50d9e276daeb66a9908158a8d25a853897a18bdce5ef528352e3dfb567c165`.
An independent ZIP inspection verified 85 inner archives, each containing only
its designated packet with the exact manifest hash; six outer operator-only
files contain the handoff/specification/freeze/template/manifest/start instructions.
Exports are not access-control sandboxes; manual isolation/routing review is
still required. Historical model availability was not directly verified.

The current working tree still has zero active `*.output.json` judgments and no
`corrections_v2/results/` directory. Historical artifacts, scientific tag and
branch HEAD remain unchanged; no push, merge, publication or inference occurred.
Live scientific estimates, dynamically selected residual jobs and resolver jobs
remain pending until genuinely fresh complete judgments and provenance exist.
Their generation and downstream analysis have been exercised only in isolated
synthetic fixtures. The dated protocol is explicitly post hoc, not a registration
of the original study; coauthor review and model-routing/isolation verification
remain manual pre-dispatch steps.
