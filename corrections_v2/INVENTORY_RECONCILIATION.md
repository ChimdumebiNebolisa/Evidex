# Historical inventory reconciliation: 775 = 774 + 1

The reviewed inventory at commit `0cc36f04ce8bbfd2a62848760c71550242be78c4`
contained 775 entries. Comparing its keys with `baseline/historical_inputs.json`
shows exactly ONE excluded/moved entry and no newly introduced historical entry:

| Reviewed inventory path | Current path | Integrity gate |
|---|---|---|
| `corrections_v2/generated/historical_pages_used.json` | `corrections_v2/inputs/historical_pages.json` | `provenance.verify_snapshot()` against `baseline/page_snapshot.json` |

It was a correction-owned exported page snapshot, not a historical experiment
file. It is still required and checked; the count change does not remove coverage.
All other 774 recorded raw hashes are copied unchanged into the immutable
historical inventory, alongside source-commit blob/LF identities.

Snapshot identities:

- Original acquisition raw SHA-256:
  `b6848f9d053ec6451186b384c0661894448049c68df48de728c0596b2e240f98`.
- Reviewed Git blob / current UTF-8 LF SHA-256:
  `70164565d89ef48b634e06b8150b1fdfc74f219ddbf25e96f387387fc51eb55a`.
- Both are retained in `baseline/page_snapshot.json`; acquisition provenance also
  remains in `inputs/archive_provenance.json`.

`reproduce.py`, `verify_outputs.py`, and the analysis pipeline preparation gate
check the snapshot before output generation. Only CRLF-to-LF text equivalence is
permitted; substantive changes fail. `generated/snapshot_integrity.json` reports
the observed identity separately from the 774-file historical report.

The regression test `ConsensusStatisticsTests.test_inventory_reconciliation`
loads the actual reviewed Git inventory, asserts its 775 entries, asserts the
exact one-path set difference, checks all retained raw hashes, and verifies the
moved snapshot. Run:

```powershell
python -m unittest discover -s corrections_v2/tests -p test_analysis_pipeline.py -v
```

No historical manifest or artifact tag was rewritten.
