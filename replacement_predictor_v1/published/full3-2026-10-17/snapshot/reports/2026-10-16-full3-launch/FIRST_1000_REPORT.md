# Full3 first 1,000-job report — 2026-10-16

Full3 is running under the existing twenty-worker launcher, operator600 configuration and $35 forecast supervisor. Both models passed metadata access checks. No new smoke or paid benchmark was performed. The seals verified before launch and again at this checkpoint.

The first checkpoint observed at least 1,000 completed jobs at 2026-10-17T00:36:29.403265+00:00: **1,006 valid, zero invalid, zero failed, zero uncertain and zero retries**. The run continued after the checkpoint; these are checkpoint counts rather than a claim that the full experiment is complete.

| Model | Full3 completed calls | Prompt tokens | Completion tokens | Usage-derived cost |
|---|---:|---:|---:|---:|
| gpt-5.4 | 516 | 36,563 | 2,514 | $0.12911750 |
| gpt-5.4-mini | 490 | 33,869 | 3,190 | $0.03975675 |

Recorded full3 usage cost was **$0.16887425**. Six submitted calls were still awaiting usage, with **$0.00507875** conservatively reserved. The forecast for full3 was **$30.15**, below the **$35** admission-stop threshold. Earlier smoke cost is separate; this is a token-usage calculation at checked standard rates, not a reconciled invoice.

The trailing 60-second checkpoint window contained **341 successful calls** while ramping. The configured aggregate target is 600 RPM with 600,000 reserved TPM, twenty workers and the same SQLite queue/run directory. Snapshot policy and recent launcher ETA are preserved in the JSON companion. The five-to-six-hour estimate remains conditional; undisplayed limits, cooldowns and latency can extend execution.

No halt or monitor error was active at report creation. The local supervisor continues independently of chat polling and requests coordinated draining if projected total cost exceeds $35 or monitoring fails. Existing authentication, quota, parameter and unexpected-model halts remain sticky. Invalid and uncertain jobs are not replaced. Every request and raw response continues to be recorded through the unchanged runner.

Files: `FIRST_1000_REPORT.json` records the exact checkpoint, current progress, usage, limits/seal hashes and supervisor PID. The original milestone is retained in the supervision directory identified there. The 48 original smoke artifacts still match their hashes. No frozen scientific/worker implementation or previous seal was changed during launch.

What changed: launched the authorized full3 run with existing operator600 settings and the sealed cost supervisor. Files changed: only launch/access/raw-response/progress artifacts and this report. Verification run: seal checks, metadata access, live checkpoint/worker/ledger checks and preservation of smoke artifact hashes; 78 mocked/regression tests passed before launch. Result: first 1,000 completed, full3 continues. Remaining uncertainty: eventual usage, unexposed provider limits and completion time.