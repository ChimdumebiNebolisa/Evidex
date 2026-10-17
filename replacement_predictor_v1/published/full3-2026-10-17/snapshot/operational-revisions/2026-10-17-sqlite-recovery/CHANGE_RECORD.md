# SQLite operational recovery — 2026-10-17

This additive operational revision repairs local SQLite contention in the existing full3 run. All prior implementation files and seals are retained unchanged. The frozen experiment, prepared order, prompts, models, settings, parsing, acceptance rules, API retry eligibility/counts, uncertainty handling and raw-response recording are unchanged.

## Diagnosis and evidence

The incident traceback confirms `SQLITE_BUSY` at `BEGIN IMMEDIATE` in `Coordinator.record`, after the response artifacts had been saved. Original launcher recovery reconstructed `51856_gpt-5.4_C_r03` from those saved artifacts and returned eight jobs without request files to pending. The database stopped with 41,446 valid and 138,554 pending jobs, no in-flight jobs, and $6.86945225 recorded usage cost. The $35 forecast guard did not cause this stop.

Confirmed sources of writer contention in the original code:

- Admission polling acquired a write transaction even when pacing prevented admission. Twenty workers could repeatedly compete for the single writer while waiting.
- Response recording held its write transaction while scanning the populated attempt history twice for outstanding request/token budgets. On a stopped-database clone, the original query scanned 41,446 ledger rows and averaged about 44 ms per query. Adding generic indexes alone did not improve it.
- Job claims and state/meta updates also use write transactions. Claim transactions include local file-lock/artifact checks.
- Connections used a 30-second SQLite busy timeout with no statement-level bounded retry after timeout.

The budget monitor's routine snapshot is a read transaction in WAL mode, not a routine writer. Initialization DDL and stop updates can write. The historical logs do not identify the precise lock owner or prove one transaction held the lock for 30 seconds; unfair repeated contention and long-reader/checkpoint effects remain possible explanations, not established causes. The reproduction demonstrates the failure class and the repair, not the incident's exact scheduling.

See `QUERY_PROBE.json`, `PARTIAL_INDEX_PROBE.json`, `RED_TEST_RESULTS.txt`, `COORDINATOR.diff` and `AST_CHECK.json` for evidence. Probe timings are local diagnostics, not a promised live throughput benchmark.

## Minimal selected runtime

`sqlite_supervisor.py` selects the original launcher, Store, transport, parser and budget supervisor with two explicit operational substitutions. Windows spawned workers import the same selection before running the original worker function.

`sqlite_coordination.py` preserves the original coordinator except for connection selection, a read-only pacing fast path, and the response-recording outstanding-budget query. Actual admissions still repeat every check in the original atomic write transaction. The replacement query uses disjoint UNION arms and a partial open-attempt index; its measured mean on the populated clone was about 0.018 ms. The test checks multiset equivalence, including NULL start times. The original `Stopped` exception class is reused.

`sqlite_runtime.py` retries individual SQL statements only on SQLite BUSY/LOCKED, using a short 100 ms engine wait, jittered 5–50 ms waits, and both a 45-second and 200-retry bound. It never wraps or replays an API call or a transaction body. Other SQL errors propagate. Idempotent schema statements are retried individually. Connection/transaction wait diagnostics are appended under the run's `sqlite-runtime` directory without SQL parameters or credentials. Durable responses remain subject to the unchanged original recovery rules if retry bounds are exhausted.

## Preservation and validation

`BACKUP.json` records a consistent SQLite online backup made from the stopped read-only database before changes, its file hash, matching source/backup logical fingerprint, integrity check, baseline spending, source hashes and previous seals. The backup is retained in `backup/jobs.sqlite`. `PROCESS_CHECK.json` records that old experiment processes had exited before backup/repair.

The two pre-fix reproductions fail on database locking. The new mocked tests exercise read-only polls behind a held writer, SQL-only retries after response receipt, bounded exhaustion and response recovery, unrelated SQL failures, reset/cooldown precedence and duplicate admission protection, query equivalence, and a 20-process test against a clone of all 180,000 queue rows and 41,446 prior admissions. That test records 120 mocked responses with concurrent budget monitoring, deliberate writer contention, interruption, draining, recovery and restart; it verifies one transport call/admission per selected job, preserved raw hashes and cumulative spending. Existing limiter, global-halt, retry and recovery tests also run under the selected runtime. Exact outcomes are retained in `TEST_RESULTS.txt` and `MOCK_STRESS.json`.

Verification command: `python -B replacement_predictor_v1/tests/run_sqlite_revision_tests.py`. All 85 tests passed in 281.120 seconds. The populated-clone stress recorded 120 responses, zero duplicate admissions, 266 handled database retry events and a maximum measured transaction duration of 7.063 seconds under deliberate contention and concurrent disk-heavy validation. This is evidence of bounded handling, not a claim that all live transactions will be fast. The existing 20-worker late-queue test also passed against 179,880 prior ledger rows. No paid inference was used for validation.

`reconcile.py` checks the stopped production database read-only, all prepared jobs/order/payloads, original seals, every saved request/hash/settings, receipt/raw hash, frozen interpretation and ledger usage/state, response IDs, duplicate admissions, cumulative cost, the recovered response and the eight no-request returns. `ARTIFACT_INVENTORY.jsonl` preserves hashes of every existing attempt artifact. `RECONCILIATION.json` must say PASS before launch; uncertainty is not converted into permission to resend.

Production reconciliation passed at 2026-10-17T08:50:28 UTC: 180,000 unique planned jobs, 41,446 valid responses/admissions, 138,554 pending, zero in-flight/invalid/failed/uncertain jobs, zero duplicate admissions/response IDs/raw hashes, and 165,792 attempt artifacts hashed. The recovered response passed frozen reparse/provenance checks; the eight returned jobs each retain an ordinal-1 recovery artifact and have zero request files. Recorded tokens are 2,971,524 prompt and 223,419 completion, with reported cached/reasoning counts zero. Usage-derived recorded cost is $6.86945225, not an independently reconciled invoice. All prior source hashes and seals match. The final pre-resume check is saved separately in `PRE_RESUME.json`.

## Authorized recovery and monitoring

After tests, reconciliation and seal checks pass, the selected entry point permits only this reconciled operational stop to be cleared through the original launcher's normal `--resume` path. A sticky defined halt, different stop, changed queue or failed reconciliation blocks launch. Previous completed jobs and all spending remain in the same database.

```powershell
python -B C:\Users\Chimdumebi\evidex\replacement_predictor_v1\sqlite_supervisor.py --live --resume
```

Use the already configured local key without printing it. This command resumes the same `runs/full3` queue with 20 workers and the unchanged operator600 configuration. It ramps again from 60 toward 600 total RPM, respects observed lower limits, token budgets, cooldown/reset/Retry-After headers and adaptive throttling. Shared/project/daily limits remain unknown. The original supervisor checks the cumulative projected total every two seconds and pauses admissions above $35 or on monitor failure; it includes the prior $6.86945225, all new reported usage and conservative reservations. It lets recording drain safely. No budget or defined halt may be bypassed.

The entry point is deliberately bound to this reconciled incident. A future halt requires inspection and a fresh documented reconciliation; it is not cleared automatically. Runtime diagnostics establish future lock wait/hold evidence that the original incident lacked.

After collection is terminal and all recording/recovery has drained, verify full artifact/usage/seal coverage and run the original frozen `analyze.py` into a fresh timestamped output directory, preserving 2,000 bootstrap draws. Do not run the old pre-inference `verify_release.py`, overwrite artifacts or analyses, or repair invalid/uncertain outcomes by rerunning them.
