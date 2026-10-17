# Full3 operational stop

The run stopped after **41,446 valid completions**, leaving **138,554 pending** and no in-flight jobs. A worker raised `sqlite3.OperationalError: database is locked` while recording a response; the launcher coordinated stopping and recovery. The deeper cause of the lock contention is not yet established.

Recorded token-usage cost is **$6.86945225** and the last full-run forecast is **$29.82070637**. The $35 budget guard did not trigger. No invalid, uncertain or failed API outcomes were recorded. All 41,446 admissions have finished and usage is reported; no job has multiple admissions. These are ledger checks, not a claim that every partial-run artifact has undergone the final full inventory.

Recovery reconstructed one saved valid response and returned eight jobs without request files to pending. The reconstructed response's request hash, raw response hash and frozen interpretation all verify. SQLite integrity and all seals verify. Every original attempt and recovery record is preserved.

No analysis was started because the planned work is incomplete. No new launcher was created, no stop flag was cleared, no completed job was restarted and no experiment/source/settings/acceptance/retry rule was changed. The follow-up is being paused because the operational contention requires resolution before continued inference. Existing full-run authorization remains recorded; no additional funding approval is requested.

What changed: operational stop reported; original artifacts unchanged. Files changed: this report and its JSON evidence only. Verification run: supervisor/launcher logs, drained states, ledger coverage/usage, database integrity, seal checks and recovered-response provenance/interpretation. Result: incomplete, safely drained. Remaining uncertainty: deeper contention cause and safe operational remedy before resumption.
