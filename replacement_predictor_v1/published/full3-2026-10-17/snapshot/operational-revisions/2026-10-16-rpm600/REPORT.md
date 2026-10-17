# Full3 throughput revision delivery — 2026-10-16

The existing twenty-worker launcher now supports a gradually ramped, adaptive **600 total RPM** target across both frozen models. No paid calls were made. **Full3 remains unstarted: 180,000 pending jobs, zero admissions and zero request artifacts.**

## Effective limits

| Scope | RPM | TPM | Evidence |
|---|---:|---:|---|
| GPT-5.4 account/model | 5,000 | 1,000,000 | Preserved smoke headers; user Limits-page report |
| GPT-5.4-mini account/model | 5,000 | 2,000,000 | Preserved smoke headers; user Limits-page report |
| New aggregate target | 600 | 600,000 | Operational target, conditional on shared capacity |
| Currently enforced fallback | 60 | 60,000 | Previous conservative operational ceiling |

**The 600 target is implemented and tested but is not activated by the supplied candidate.** Shared-family, project/organization aggregate and daily limits remain unverified. The accessible dashboard was signed out; no local API/admin credential was configured. The per-model caps do not prove aggregate/daily capacity. No repeat smoke or paid benchmark was performed.

Before selecting capacity above 60 RPM, create a separately dated copy of the candidate and record verified shared RPM/TPM evidence in `rate_policy.capacity_evidence`, setting `verified` true. Record any applicable daily caps as `rpd`/`tpd` on the corresponding bucket. Select that file with `--limits`. Preserve the sealed candidate. Lower verified caps and response-header budgets remain binding.

## Operational changes and preservation

- One existing launcher, twenty processes, the same full3 directory and SQLite queue. No runner rebuild.
- Shared ramp of 60/120/240/360/480/600 RPM at one-minute steps, positive 1–9 ms jitter, rolling request/token budgets and conservative prepared-request reservations.
- Transient throttling halves the shared rate, with a 15-RPM floor. Successful traffic recovers at most 60 RPM per minute. Shared cooldowns and Retry-After/remaining/reset headers continue to bind; restart retains cooldowns and adaptive penalties and restarts the ramp.
- Faster blocked-worker admission checks, a queue index and an atomic cumulative admission counter avoid rescanning the entire ledger for each waiting worker. Known exhausted header/reset waits remain authoritative.
- Existing durable response recording, retries, global halts, interruption/recovery, uncertain-transmission handling and duplicate prevention are retained. Progress includes current/target RPM and capacity evidence status.
- Original protocol and first operational seals/configuration are unchanged. Three superseded operational files are archived; the new seal verifies the complete chain. Existing full3 run identity and prior operational binding are unchanged; a separate throughput binding is added.

Claims, requested/accepted models, messages, settings, conditions, repetitions, randomized prepared order, parsing, analysis and acceptance rules are unchanged. `runner.py` is byte-identical to the first operational revision. Common scientific definitions match that revision's AST after excluding the operational freeze verifier. Every queued job and ordinal matches the frozen plan. All 48 preserved smoke artifacts match their hashes.

Token reservations average 346.1993 per request, with a maximum of 2,193. The maximum sum over 600 consecutive planned jobs is 220,166; the 600,000 reserved TPM target includes headroom and remains below each advertised model TPM cap. All attempts, including failures and uncertainty, remain charged against admission budgets.

## Verification

**62 tests passed in 93.278 seconds**, covering the original scientific/runner tests, existing operational tests and fourteen throughput tests. Coverage includes aggregate enforcement with twenty processes, rolling token/daily budgets, shared cooldowns, provider resets, adaptive reduction/recovery, authentication/quota/parameter/model halts, interruption/recovery and duplicate prevention.

The physical twenty-process mocked fixture used a 180,000-row queue and ledger, including 179,880 synthetic prior terminal rows and seeded provider header budgets. It recorded **120 distinct valid synthetic responses**, no duplicates, mean admission interval **0.111912 seconds**, about **536.13 RPM**, and **2.58 seconds** startup to first admission. Its mock transport sleeps 0.15 seconds. This measures local overhead, not sustained provider capacity.

The existing end-to-end mock integration also passed: 36 planned synthetic jobs, 34 valid, one intentionally invalid and one intentionally missing; raw artifacts, retry failure coverage, analysis and CSV outputs verified. Database integrity and `git diff --check` passed. No paid generation or access calls were used for this revision.

## Runtime and cost

| Scenario | Projected runtime |
|---|---:|
| Arithmetic floor at sustained 600 RPM | 5.00 hours |
| Conditional 600 target, smoke mean latency and measured local overhead | **5.66 hours** |
| Conditional 600 target, twice smoke mean latency | **6.23 hours** |
| Conditional 600 target, 10% more attempt time | **6.23 hours** |
| Active candidate at unverified-capacity fallback | **50.62 hours** |

The two 6.23-hour scenarios are separate sensitivities, not a confidence interval or combined upper bound. Throttles, cooldowns, daily caps, concurrent account traffic, provider long-tail latency, interruptions and retries can extend execution. The simulation uses the existing randomized job plan, operational pace/ramp functions, worker occupancy, jitter, capped polling waits and an incremental overhead calibration against the matched mock fixture. Smoke mean latencies are 1.4148 seconds for GPT-5.4 and 0.9030 seconds for GPT-5.4-mini. Twelve calls on two claims cannot establish sustained throughput or full-population usage.

Existing smoke usage-derived cost: **$0.0021275**. Full3 projection: **$29.6787**, or **$32.6466 with 10% more billable attempts**. Prices remain the frozen standard rates: GPT-5.4 $2.50/$15 and GPT-5.4-mini $0.75/$4.50 per million input/output tokens. This is token-based extrapolation, not an independently reconciled billing invoice. Throughput changes do not alter the scientific requests or token prices. Only the original **$5** funding is confirmed.

Remaining launch requirements are verified applicable shared/project/daily limits, adequate funding for the projected cost with contingency, a locally configured API key and **separate explicit authorization for full3**. No full-run authorization is inferred from this delivery.

## Exact launch and resume commands

The commands below select the sealed candidate, which currently stays at the 60-RPM fallback. For the conditional 600 target, set `$limits` to the separately dated, evidenced capacity configuration before the future authorized launch. Both launch and resume must use the same run directory; never prepare a replacement queue to improve completion counts.

```powershell
$exp = 'C:\Users\Chimdumebi\evidex\replacement_predictor_v1'
$limits = "$exp\operational-revisions\2026-10-16-rpm600\limits-600.json"

# Read-only status; no model requests:
python -B "$exp\launcher.py" status --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits"

# Only after separate full-run authorization, sufficient funding and account checks:
python -B "$exp\launcher.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000

# Resume the same authorized run after coordinated interruption:
python -B "$exp\launcher.py" run --live --resume --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000
```

The cumulative cap of 540,000 preserves the existing maximum three request-bearing attempts per job. It does not increase retries, change eligibility or authorize replacing invalid/uncertain results. Ctrl+C drains in-flight recording; sticky authentication, quota, parameter or model halts require inspection and are not cleared automatically by resume.

## Files and evidence

Changed operational source: `common.py`, `coordination.py`, `launcher.py`. New source: `rate_policy.py`, `throughput_projection.py`, `seal_throughput.py`, `tests/test_throughput.py`. Dated configuration, archive, change record, runbook, evidence and test log are in this revision directory. `runner.py`, previous configurations, previous seals and scientific files were not changed by this revision.

`revision.json` seals implementation and prospective evidence. `PROJECTION.json`, `VERIFICATION.json` and this delivery report are derived after sealing; they do not replace a prior artifact. The new seal SHA-256 is `7d078a48091fe9763cc691790fb11935bd2107e8fce3bf25d6baa75886200155`.

Primary references: [OpenAI rate-limit guide](https://developers.openai.com/api/docs/guides/rate-limits), [standard API pricing](https://developers.openai.com/api/docs/pricing). Account evidence comes from saved receipts and the user's Limits-page report, not public tier assumptions.
