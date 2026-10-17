# Full3 operational throughput configuration

Full3 remains unstarted: 180,000 prepared jobs, 20 processes, one run directory and one SQLite queue. This revision changes scheduling only. The prior protocol and worker revision seals/configuration are preserved.

## Effective capacity and launch requirements

Saved smoke response headers and the user's Limits-page report agree:

| Scope | RPM | TPM |
|---|---:|---:|
| GPT-5.4 | 5,000 | 1,000,000 |
| GPT-5.4-mini | 5,000 | 2,000,000 |
| Configured aggregate target, conditional | 600 | 600,000 |
| Current fallback while shared capacity is unverified | 60 | 60,000 |

The available dashboard browser was signed out. No accessible local API/admin credential was configured at this check. Shared-family, project/organization aggregate, daily request/token limits and current spendable balance could not be verified. No paid access check or repeat smoke is authorized. These per-model figures alone do not establish every aggregate/daily limit. Provider headers can lower effective capacity; they cannot establish the absence of unexposed limits. See the [OpenAI rate-limit guide](https://developers.openai.com/api/docs/guides/rate-limits).

To enable the higher target, first record evidence of applicable aggregate/project capacity. Create a **separately dated copy** of `limits-600.json`, set `capacity_evidence.verified` true, provide its source and verified shared RPM/TPM, and include any applicable daily ceilings as `rpd`/`tpd` on the appropriate bucket. Preserve this sealed candidate. Supply that copy with `--limits`. Verified capacity below 600 RPM or 600,000 TPM reduces the effective ceiling; never claim it supports the conditional 600-RPM projection. No new code or scientific change is needed.

The token reservation includes prepared message UTF-8 bytes, 32 completion tokens and 32 framing tokens: mean 346.1993, maximum 2,193 per call. Maximum any 600 consecutive planned requests is 220,166 reserved tokens. The 600,000 TPM operational capacity therefore includes substantial headroom; rolling budgets and per-request pacing also enforce it if concurrent completions alter admission order. Reservations remain charged for failures and uncertainties.

Ramping uses shared steps 60/120/240/360/480/600 RPM, one minute each, with 1–9 ms positive randomized jitter. Theoretical 180,000/600 = five hours excludes ramp, jitter, worker/queue overhead, latency and retries. `PROJECTION.json` (a derived output created after sealing) contains actual scheduling estimates and sensitivity to latency. Throttling halves the shared rate, honors shared Retry-After/reset cooldowns, and recovers only with successful traffic, at most 60 RPM per minute. All twenty workers use the same database state.

The usage-derived existing smoke cost is $0.0021275. The full3 usage extrapolation is approximately $29.68, or $32.65 with 10% more billable attempts. This is a two-claim projection, not a billing guarantee. Throughput does not reduce token charges. Only the original $5 funding is confirmed; more funding and **separate explicit authorization for full3** are required. Reconfigure the local key securely only at that future authorized launch. Do not paste it into chat or a file tracked by Git.

## Exact commands

These commands select the preserved candidate; it stays at the 60-RPM fallback until an evidenced dated copy is selected. `prepare`, `status` and `recover` do not call models. Do not execute either `run --live` command without new full-run authorization and sufficient funding.

```powershell
$exp = 'C:\Users\Chimdumebi\evidex\replacement_predictor_v1'
$limits = "$exp\operational-revisions\2026-10-16-rpm600\limits-600.json"

python -B "$exp\launcher.py" prepare --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits"
python -B "$exp\launcher.py" status --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits"

# Future authorized launch (select an evidenced dated limits copy for >60 RPM):
python -B "$exp\launcher.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000

# Future authorized resumption, same directory, plan and selected limits:
python -B "$exp\launcher.py" run --live --resume --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000
```

540,000 is the existing worst-case cumulative admission cap (three per prepared job), not permission to spend that amount or to replace invalid responses. Ctrl+C requests coordinated draining; allow in-flight calls to finish recording. Resume preserves completed responses, never resends uncertain transmissions and does not clear sticky authentication, quota, parameter or model-identity halts. Such halts require inspecting the retained evidence first. Original retry eligibility is unchanged.

Reproduce verification with `python -B -m unittest discover -s "$exp\tests" -p 'test_*.py' -v` and `python -B "$exp\tests\run_mock_integration.py"`. The twenty-process fixture is synthetic and cannot make API calls. Recalculate the offline projection into a new output filename with:

```powershell
python -B "$exp\throughput_projection.py" --limits "$limits" --benchmark "$exp\operational-revisions\2026-10-16-rpm600\MOCK_BENCHMARK.json" --output "$exp\operational-revisions\2026-10-16-rpm600\PROJECTION-next.json"
```
