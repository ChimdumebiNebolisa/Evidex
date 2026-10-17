# Full3 SQLite recovery and first post-resume checkpoint

The existing full3 queue resumed under supervisor PID 44500 with 20 workers and the unchanged operator600 configuration. The $35 projected-total guard retains all prior spending. Collection is ongoing; final artifact verification and the original frozen analysis remain pending collection completion. The existing bounded follow-up is ACTIVE.

## Diagnosis and operational change

The traceback confirms a worker timed out acquiring BEGIN IMMEDIATE in response recording after its raw response was already saved. The exact historical lock owner is not established. Confirmed avoidable contributors were write transactions for blocked admission polls and repeated full-ledger scans inside response-recording transactions. Job claims and state/meta updates also compete for the single SQLite writer. Routine budget snapshots are WAL read transactions; monitor initialization/stop updates can write. A claim about the precise historical transaction duration would exceed the evidence.

The separately sealed revision uses read-only blocked polls, an equivalent indexed outstanding-budget query, and bounded, jittered retries of individual BUSY/LOCKED SQLite statements. It never repeats an API request or transaction body. Existing response persistence, recovery, scientific settings, parser, acceptance rules and API retries are unchanged. Original active files and every previous seal remain intact. The new seal is `1a12071ba5b530bb49cb57adecafcc7dc0238162cf0b3ad9b31b7585a5a3cf87`.

A consistent stopped-database backup was preserved before changes. SQLite integrity, matching backup/source logical fingerprints and all previous seals passed. The new entry point cleared only the reconciled operational stop through the original --resume path. Other defined halts remain binding.

## Offline validation and pre-resume reconciliation

All 85 mocked tests passed, including 20-process aggregate pacing, token budgets/cooldowns, defined halts, response recording under a held writer, bounded retry exhaustion, recovery without API resend, monitoring, interruption and duplicate prevention. The populated clone had all 180,000 jobs and 41,446 prior admissions; 120 mocked responses survived interruption and recovery with zero duplicate admissions. The existing late-queue test with 179,880 prior ledger rows also passed. Two pre-fix lock reproductions failed as expected. No paid validation calls were made.

The read-only production reconciliation verified 180,000 unique prepared jobs/order/payloads, 41,446 valid saved responses/admissions, 138,554 pending jobs, zero in-flight/failed/invalid/uncertain jobs, 165,792 attempt-artifact hashes, no duplicate admissions/provider response IDs/raw hashes, and frozen interpretations and usage accounting. The recovered response passed. Each of eight returned jobs retained its original recovery record and had no request file. The cumulative recorded cost reconciled to $6.86945225. All old experiment processes had exited and ownership locks were free before resumption.

## First checkpoint — 2026-10-17 08:54:52 UTC

| Measure | Checkpoint |
|---|---:|
| New valid completions after resumption | 244 |
| Total valid jobs | 41,690 |
| Pending jobs | 138,290 |
| Claimed/in-flight jobs, including workers waiting for admission | 20 |
| Admissions awaiting a recorded outcome | 3 |
| Failed, invalid or uncertain terminal jobs | 0 |
| Duplicate admissions | 0 |
| Finished attempts without reported usage | 0 |
| Recorded prompt tokens | 2,989,686 |
| Recorded completion tokens | 224,686 |
| Reported cached / reasoning tokens | 0 / 0 |
| Recorded undiscounted token-usage cost | $6.91165825 |
| Additional recorded cost since incident | $0.04220600 |
| Projected full-run total, including reservations and remaining work | $29.82243334 |
| Budget guard | $35 |
| Selected target / current ramp stage | 600 / 240 RPM |
| Successful calls over preceding minute | 165 |
| Workers alive | 20 |

The recovered response has not been resubmitted. All eight safely returned jobs are now valid, with exactly one actual request and one admission each at ordinal 2; ordinal 1 contains only the preserved no-request recovery record. Their earlier recovery files and the recovered response artifacts were rehashed unchanged. All baseline completed states, prepared payloads/order and admission-ledger rows still match the backup.

At the checkpoint 530 transient SQLite busy events had been handled without retry exhaustion. Maximum logged wait was 2.328 seconds. Maximum logged transaction duration was 9.141 seconds across reads and writes; the longest entries were in the supervisor process, whose routine budget projection holds a read transaction. The logger does not label transaction mode, so this is not proof of a 9-second writer hold. A subsequent inspection measured maximum worker transaction duration of 2.062 seconds. Remaining contention and monitor computation time are observable operational constraints; the configured two-second monitor wait is additional to snapshot computation, not a guarantee of precisely two-second sampling.

## Continuation and limits

Exact command used (already running; do not launch a duplicate):

```powershell
python -B C:\Users\Chimdumebi\evidex\replacement_predictor_v1\sqlite_supervisor.py --live --resume
```

The same run directory and queue are retained. Shared/project/daily provider limits remain unverified; lower observed limits, cooldowns, token budgets, adaptive throttling and local overhead can reduce throughput. Early ramp throughput does not establish sustained runtime. Cost is calculated from reported tokens at the frozen rates with no cache discount; it is not an independently reconciled invoice. In-flight or future unreported usage remains reserved by the original guard.

The active follow-up will inspect the existing supervisor and finish full artifact/accounting verification and the unchanged 2,000-bootstrap frozen analysis only after all jobs are terminal and recording/recovery has drained. It must stop and report any future operational, budget or defined halt rather than clear it automatically. No analysis or original artifact has been overwritten.

What changed: operational SQLite recovery and same-queue resumption. Files changed: additive sqlite_runtime.py, sqlite_coordination.py, sqlite_supervisor.py, two test files, the separately sealed operational revision and this report/checkpoint; existing implementation files unchanged. Verification run: 85 offline tests, consistent backup, full stopped-run reconciliation, old/new seal verification and the live checkpoint. Result: running with 20 workers and cumulative $35 guard. Remaining uncertainty: exact historical lock owner, sustained throughput and final study outcomes; final verification/analysis await completion.
