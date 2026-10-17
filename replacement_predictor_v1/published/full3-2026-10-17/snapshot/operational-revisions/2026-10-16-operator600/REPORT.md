# Operator-selected full3 target — 2026-10-16

The selected operational target is **600 total requests per minute across the existing 20 workers**, with **600,000 reserved tokens per minute shared across both models**. The existing limiter ramps 60 / 120 / 240 / 360 / 480 / 600 RPM at one-minute steps, reaching the target after five minutes if observed budgets and adaptive throttling permit. The initial 60-RPM ramp stage is not a permanent fallback.

This is a configuration-only change. The existing limiter already supports operator-selected unverified-capacity ceilings through `unverified_shared_rpm` and `unverified_shared_tpm`; the new dated configuration sets these to 600 and 600,000. `operator_target` explicitly identifies them as the user's operational selection. **`capacity_evidence.verified` remains false**, shared RPM/TPM remain null, and unknown shared/project/daily provider limits remain unknown. No provider capacity has been invented or newly verified.

Confirmed per-model ceilings remain 5,000 RPM / 1,000,000 TPM for GPT-5.4 and 5,000 RPM / 2,000,000 TPM for GPT-5.4-mini, from the preserved smoke headers and user Limits-page report. These are retained as model buckets and evidence metadata. The shared operational bucket is stricter. All workers use the same run directory, SQLite queue and limiter.

Observed lower model/project/organization limits, remaining/reset budgets, Retry-After and shared cooldowns still bind. The unchanged adaptive policy halves the shared rate on transient rate-limit 429 or 503 responses, with a 15-RPM floor, and restores at most 60 RPM per minute on successful traffic. Restart retains penalties/cooldowns and restarts the ramp. Reservations include completion allowance and are not refunded for failed or uncertain attempts.

No changes to implementation, claims, models, requests, messages, settings, repetitions, randomized prepared order, parsing, scientific analysis, retries, acceptance rules, global failure handling, uncertain transmissions or raw-response recording. No completed job is restarted. Both earlier configurations, all three previous seals and the twelve-call smoke artifacts are preserved. The new independent configuration seal references their hashes without replacing any seal or existing run binding. The launcher records the exact selected configuration on a future launch.

## Verification

**All 68 tests passed in 101.885 seconds.** The new six-test module exercises the actual selected configuration with false capacity evidence: ramp to 600, confirmed model caps and unknown aggregate limits, lower observed headers, aggregate token budgets, shared cooldown/adaptive reduction, twenty-process contention, duplicate prevention and global halts. Existing mocked operational/throughput tests also cover recovery, interruption, uncertain transmission, retry limits and durable response recording. Full results are in `TEST_RESULTS.txt`; final integrity checks are in `VERIFICATION.json`.

## Exact future launch command

Use this new dated configuration explicitly. The unchanged launcher's default still identifies the original preserved configuration.

```powershell
$exp = 'C:\Users\Chimdumebi\evidex\replacement_predictor_v1'
$limits = "$exp\operational-revisions\2026-10-16-operator600\limits-operator600.json"

# No inference: inspect the selected configuration and existing queue.
python -B "$exp\launcher.py" status --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits"

# Future launch only after sufficient funding and separate full-run authorization:
python -B "$exp\launcher.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000

# Future resumption of that authorized run, same directory and selected configuration:
python -B "$exp\launcher.py" run --live --resume --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000
```

The cumulative 540,000 admission cap preserves the existing maximum three request-bearing attempts per planned job; it does not change retry eligibility or permit replacement of invalid or uncertain results. Sticky access, quota, parameter or model failures remain sticky. Ctrl+C requests coordinated draining and preserves in-flight recording.

## Remaining limits and authorization

**Undisplayed shared/project/daily limits may reduce throughput.** The five-to-six-hour estimate is conditional, not a guaranteed completion time: the previous offline 600-target estimate was 5.66 hours using saved smoke latency, pacing, jitter and local worker overhead; twice the smoke mean latency gave 6.23 hours. Cooldowns, retries, daily caps, concurrent account traffic or provider latency may extend execution further. No new paid benchmark or smoke was performed.

The existing cost projection remains approximately **$29.68**, or **$32.65 with 10% more billable attempts**. Only the original **$5** funding is confirmed. Additional funding, a locally configured API credential and explicit full-run authorization remain outstanding. **No paid calls were made and full3 was not launched.**

Files added for this selection: `limits-operator600.json`, `BASELINE.json`, this report, the test log, the independent `revision.json` configuration seal, `VERIFICATION.json`, and `tests/test_operator_target.py`. Existing files are unchanged by this selection. Old reports describe historical configurations; this report and the new explicit `--limits` path supersede their selection advice.
