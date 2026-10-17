# Operational revision 2026-10-16-workers20

Purpose: add a monitored 20-process launcher, coordinated request/token throttling, shared cooldowns, global stops, operational progress and safe recovery/resumption to the existing full3 experiment.

The original `protocol-freeze.json` SHA-256 remains `2dcd6ee8877201c7c96d3413768ac6db9718403cadbda4410a56267e859af676`. It is never overwritten. Its original `common.py` and `runner.py` bytes are preserved in `original/` and checked against their original hashes. A new exclusive `revision.json` records the new files/hashes and an independent UTC seal time. The operational verifier validates both generations. A sealed revision cannot be silently re-sealed after edits.

Changed original frozen files:

- `common.py`: verify the original archived bytes and the separately sealed active operational files.
- `runner.py`: add persisted job retry eligibility time, consult the shared stop before claiming, report durable feedback before requeueing, account for uncertain transport without refunding reservations, and route live/recovery CLI use through the launcher. The request factory, parser, returned-model allowlist, retry statuses/counts, raw/receipt-before-parse ordering and exclusive writes remain unchanged.

New files: `coordination.py`, `launcher.py`, `smoke_projection.py`, `seal_operational.py`, `tests/test_operations.py`, `OPERATIONAL_LAUNCH.md`, this record, `limits.json`, original implementation copies, the revision seal and separate verification reports. The existing README links to the current operational instructions; older reports and inventories remain historical snapshots. No existing scientific analysis is replaced.

Scientifically unchanged: 10,000 inputs, both models, three conditions, three repetitions, 180,000 full3 jobs and randomized order, exact materialized messages, model settings, strict labels, independent raw analysis, representative subset/historical labels, original price estimates and the separate existing 12-job smoke. All original frozen files other than the two operational implementation files must remain byte-identical.

Operational defaults: exactly 20 child processes, one shared registered run directory, conservative shared and model ceilings, observed-header budgets, shared backoff and positive randomized pacing. No new retry class, hidden retry, invalid-output replacement, response overwrite or uncertain-call resend is introduced. Already admitted calls can finish after a shared halt; no mechanism claims to recall a request already in flight.

Live readiness is pending a locally supplied API key, successful metadata access for both aliases, verified account/shared-family limits, separately authorized paid smoke, retained-response review and measured usage/runtime/cost review. No paid smoke or main experiment is authorized by merely preparing this package.
