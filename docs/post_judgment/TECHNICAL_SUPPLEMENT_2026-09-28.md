# Technical supplement to the post-judgment analysis note — 2026-09-28

Operational detail behind `POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md`. The attempt-by-attempt
record is `corrections_v2/deviation_review/attempt_table.md`. The execution deviations and their
evidence are in `corrections_v2/deviation_review/DEVIATION_ASSESSMENT_2026-09-28.md`.

## A. Recovered WSL outputs

Failed attempts left three output files in their isolated WSL workspaces. Two were archived nowhere
else. The third, from `p01_C_j1_b02`, was already tracked as that attempt's `raw.txt`.
`corrections_v2/deviation_review/tools/recover_wsl_outputs.py` copied their exact
bytes (via `wsl -u root -e cat`, one time) into
`corrections_v2/deviation_review/evidence/recovered_wsl_outputs/<job>/attempt-01.workspace.output.json`.
Each copy was accepted only if its size and SHA-256 matched both
`evidence/unstaged_failed_outputs.json` and the earlier `evidence/wsl_inventory.json`. The
directory is byte-exact (`* -text`) and the contents were never repaired. Details are in
`recovered_wsl_outputs/manifest.json`.

| Job / slot | Bytes | SHA-256 | Parse / schema | Run outcome |
|---|---:|---|---|---|
| `p01_C_j1_b02` / 1 | 35,244 | `0bc4eaf02b17…a5a8` | invalid JSON: extra data at char 35,241 | recorded as `invalid` (trailing quote). The same bytes are already tracked as `execution/p01_C_j1_b02/attempt-01.raw.txt` |
| `p01_C_j4_b08` / 1 | 13,485 | `1d255e15e92e…b9fc` | invalid JSON: truncated at char 13,485 | ended `[resource_exhausted]` |
| `p01_C_j5_b09` / 1 | 33,544 | `184e3b68947e…11e3` | valid; 100 schema-valid rows | ended `[resource_exhausted]` after writing the file |

Source path pattern:
`/home/evidex/isolated/<job>/attempt-01/workspace/corrections_v2/blind_io/p01/stage_c/<job>.output.json`.
The error records for slot 1 of `p01_C_j4_b08` and `p01_C_j5_b09` say the output was never created.
The recovered files contradict that, and the records remain unedited.

## B. Inputs to the provisional analysis

`corrections_v2/deviation_review/provisional_analysis.py` reads only tracked, repo-relative files.
It has no absolute paths and no WSL or staging access. Before any analysis, every alternative output
is checked in four ways:

- its size and SHA-256 against constants in the script;
- against the recorded hashes (`routing.output_sha256` and `model_output.sha256` in
  `evidence/attempt_evidence.json`; the recovered manifest for the Grok file);
- for accepted slots, byte equality with the delivered `blind_io` output;
- schema validity using the frozen `rerun.validate_rows`.

| Job / slot | Tracked file | Rows | SHA-256 prefix |
|---|---|---:|---|
| `p02_C_j2_b02` / 1, 2, 3* | `corrections_v2/execution/p02_C_j2_b02/attempt-0N.raw.txt` | 77 | `6b64ed30368b`, `676a76a3226e`, `1a74c7d8efa3` |
| `p02_C_j2_b03` / 1, 2, 3, 4* | `corrections_v2/execution/p02_C_j2_b03/attempt-0N.raw.txt` | 72 | `e64e7a0db301`, `978acd62a371`, `8438ff2120c5`, `1001dbbfa31c` |
| `p01_C_j5_b09` / 1 | `corrections_v2/deviation_review/evidence/recovered_wsl_outputs/p01_C_j5_b09/attempt-01.workspace.output.json` | 100 | `184e3b68947e` |

\* accepted slot; identical to the delivered output.

## C. The 12 Claude combinations

Changed claims are counted against the accepted selection (slot 3 × slot 4). Label counts are the
Claude Stage C consensus over 226 claims.

| j2_b02 slot | j2_b03 slot | Changed | Supported / Refuted / Ambiguous |
|---:|---:|---:|---|
| 1 | 1 | 6 | 80 / 107 / 39 (first-valid) |
| 1 | 2 | 5 | 80 / 108 / 38 |
| 1 | 3 | 1 | 77 / 107 / 42 |
| 1 | 4 | 1 | 77 / 107 / 42 |
| 2 | 1 | 5 | 81 / 107 / 38 |
| 2 | 2 | 4 | 81 / 108 / 37 |
| 2 | 3 | 0 | 78 / 107 / 41 |
| 2 | 4 | 0 | 78 / 107 / 41 |
| 3 | 1 | 5 | 81 / 107 / 38 |
| 3 | 2 | 4 | 81 / 108 / 37 |
| 3 | 3 | 0 | 78 / 107 / 41 |
| 3 | 4 | 0 | 78 / 107 / 41 (accepted) |

## D. Reproducing and checking the committed results

- `python corrections_v2/deviation_review/provisional_analysis.py verify` recomputes both result
  sets and the sensitivity summary in a temporary directory, then compares them with
  `corrections_v2/deviation_review/provisional_results/`.
  - All tables, JSON files and SVG plots must match byte for byte. The only exceptions are
    `created_at_utc` in `status.json` and that file's own entry in `provisional_file_hashes.json`.
  - It also checks changed claim IDs, headline counts, all 16 test results and the 12 combinations.
  - It reports the separation check for the Grok slot-1 file described in the note.
  - It writes nothing in the repository.
- `python -m unittest discover -s corrections_v2/deviation_review/tests` runs fast input checks:
  portability, hash and schema validation, rejection of altered bytes, and confirmation that the
  recovered files are unrepaired.
- `python corrections_v2/deviation_review/provisional_analysis.py run --tag <new-date>` writes a
  new, separately named result set. It refuses the committed tag and any existing directory.

The tools in `corrections_v2/deviation_review/tools/` reconstructed the evidence on the operator's
machine and need that machine's WSL distribution or staging archive:

- `wsl_inventory.py`
- `build_attempt_evidence.py` (set `EVIDEX_STAGING_RECORDS` and `EVIDEX_RUNNER_TERMINALS`)
- `check_unstaged_outputs.py`
- `recover_wsl_outputs.py`

`render_attempt_table.py` needs only tracked evidence, and re-running it reproduces
`attempt_table.md` exactly.

## E. Items that are not artifacts

- The deleted `p02_C_j2_b02` slot-3 collision record (`attempt-03.json`, `attempt-03.routing.txt`)
  does not survive. Only the session transcript records the deletion.
- 13 execution records with session `unknown` stay `unknown`. Each one describes a duplicate
  runner invocation that exited with code 2 before launching. The run that did launch in each
  slot is identified from the slot's WSL event log and the runner log in
  `corrections_v2/amendment_2026-09-28/session_evidence.json`, not from a record.
- Failed-attempt routing files written by `sdk_execution/record_error_attempt.py` contain template
  lines. Those lines are not evidence of the run.
