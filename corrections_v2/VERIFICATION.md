# Verification record

Executed locally on the correction branch; no inference was executed.

| Check | Result |
|---|---|
| `python scripts/verify_all_headlines.py` | All Level 1 checks passed: 69/69 Analysis v2, 33/33 Grok, read-only GLM A, 38/38 Claude residual, 21/21 Claude full |
| `python scripts/run_all_tests.py` | 102 existing tests discovered; 100 passed, 2 intentionally skipped |
| `python -m unittest discover -s corrections_v2/tests -v` | 13 focused correction tests passed |
| `python corrections_v2/reproduce.py --pages corrections_v2/generated/historical_pages_used.json` | Independent behavior, exact-pointer evidence audit, raw-judgment consensus, legacy equivalence and proposed rule-only reanalysis completed |
| `python corrections_v2/audit_freezes.py` | 14 residual freeze entries accounted for; 13 text entries differ under LF-only bytes and match recorded CRLF bytes; no manifest changed |
| `python corrections_v2/build_report_data.py` | 7,585 item/judge dependency links and 10 representative cases |
| `python corrections_v2/verify_outputs.py` | 775 recorded source hashes unchanged; 1,061 exact selected sets validated; B identical; 85 C jobs complete as preparation; no corrected judgments asserted |
| `python corrections_v2/rerun.py show-job p01_C_j1_b01` | Exact model, prompt, input hash, item IDs and new output path displayed |
| `python corrections_v2/rerun.py validate` | Expected exit 1: all 85 future jobs missing; no calls launched. This is not an inference-completion result. |
| `git diff --check` | Passed; only expected Windows EOL notices |

Existing skips: a GLM test requires incomplete later-stage judgments; a residual test applies only before the already-existing manifest is written. Neither skip hides a correction test failure.

Focused tests include the actual Emperor Norton/Neil Gaiman and Singapore Airlines cases, the exported historical archive line, tab-separated hyperlink fields, NFC/NFD page titles, exact set identity, sentence order, duplicate annotation boundaries, multi-sentence evidence, unavailable selected/alternative text, canonical-text conflicts, decisive FEVER disagreement, title precedence, C-added-text interpretation and nonmonotonic judge paths.

The original-source fingerprint inventory is `generated/input_hashes.json`; corrective code fingerprints are `generated/code_hashes.json`. Prepared packet hashes are in `generated/rerun_manifest.json`. This records local files, not a pushed or committed correction release.

An initial rerun from a relative page-snapshot path exposed a path-provenance bug in the new audit script; it was fixed by resolving that input before hashing and the complete deterministic audit was rerun successfully. Superseded draft B packets are retained recoverably under `draft_archive/` and excluded from the active manifest; B inputs were preserved instead of scheduling unnecessary inference.
